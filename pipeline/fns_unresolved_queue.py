# -*- coding: utf-8 -*-
"""Очередь «нужен ИНН»: свежие стороны сделок, ещё не в реестре ФНС.

ЗАЧЕМ ЭТО ОТДЕЛЬНЫЙ ШАГ ОТ КАМПАНИИ БАТЧАМИ. Кампания 22-23 августа читала
кандидатов вручную (OKVED, регион, контекст карточки) — это единственный
надёжный способ отличить «Кама» ЦБК от «Кама» (Атом) или «Акрон Холдинг» от
завода удобрений «Акрон». Но каждая НОВАЯ карточка притока и каждая карточка,
у которой сторону только что связали со профилем (link_orphan_profiles.py,
link_named_parties_to_existing_profiles.py), заново попадает в тот же
неразрешённый список — и без повторяющегося шага он просто накапливается.
Этот скрипт — тот повторяющийся шаг: механически подтверждает только САМЫЙ
безопасный случай (единственный действующий результат с точным именем без
формы собственности), а всё остальное — в компактный список для владельца,
который сам смотрит ИНН по контексту (его прямая просьба 23 августа: «если
нужно… я сам буду смотреть»).

ПОЧЕМУ ПОРОГ УЖЕ, ЧЕМ У match_companies(auto_confirm=True). Тот путь (ещё из
Этапа 1, sync_fns.py) подтверждает по одной похожести названия (0.965 +
отрыв), без OKVED и региона — и на «Арнест» вернул 10 кандидатов с разными
ОКВЭД под похожими именами (профсоюз, санаторий, три ООО), из которых ни один
явно не главное юрлицо. Точное совпадение имени БЕЗ формы собственности
(«арнест» == «арнест», а не «арнест групп» ~ «арнест») — тоже не гарантия
(см. запись про Ярцевский завод/«ЯМЗ» в CLAUDE.md, где единственный результат
был из другого региона), но это тот же критерий, что вручную использовался в
кампании для однозначных случаев, и остаточный риск того же порядка, что и в
ручных решениях, — не хуже.

ПРИОРИТЕТ — СВЕЖИЕ СДЕЛКИ ПЕРВЫМИ (П2''/П3'' брифа). Компании сортируются по
дате САМОЙ ПОЗДНЕЙ сделки, где они упомянуты стороной, — не по числу сделок:
цель не «покрыть максимум профилей», а «у новой карточки быстро появились
финансы», а старый профиль с одной сделкой пятилетней давности подождёт.

Запуск:
    python3 pipeline/fns_unresolved_queue.py            # список, без сети
    python3 pipeline/fns_unresolved_queue.py --limit 20 --attempt --write
        # первые 20 по свежести: попытка автоподтверждения (живой поиск),
        # подтверждённое пишется в pipeline/fns_registry.py, остальное —
        # готовый текст для консоли
"""
import argparse
import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from pipeline.fns_registry import by_company_id  # noqa: E402

DATA = os.path.join(ROOT, "static", "data", "deals_promoted.json")

# Профили, у которых уже заподозрено, что это карточка-близнец другого
# профиля (Лента/«Открытие»/«Аптечная сеть 36,6» — см. комментарии партий
# 3, 4 и 6 в fns_registry.py). Решать ФНС-сопоставлением нельзя, пока
# профили не сверены и не слиты, — иначе рискуем повторить историю с «Mail»/
# «VK» (один ИНН на два профиля, тест не пропустит).
SUSPECTED_TWIN_PROFILES = {"g10f70324", "g5941cd82", "gec1422a6"}

_DISAMBIGUATOR = re.compile(r"\s*\([^)]*\)\s*$")


def clean_query_name(name):
    """Имя профиля -> строка для поиска: без наших собственных уточнений в
    скобках на конце («Кама» (Атом) -> «Кама»). Скобки внутри самого
    юрназвания (редкость) не трогаем — паттерн якорен на конец строки."""
    return _DISAMBIGUATOR.sub("", name or "").strip()


def unresolved_companies(base, registry_idx=None, exclude=None):
    """[(company_id, name, latest_date, deal_count), ...] — компании,
    упомянутые стороной сделки, ещё не в реестре, отсортированные по дате
    САМОЙ СВЕЖЕЙ сделки (убывание), внутри одной даты — по числу сделок."""
    registry_idx = registry_idx if registry_idx is not None else by_company_id()
    exclude = exclude if exclude is not None else SUSPECTED_TWIN_PROFILES
    companies = base.get("companies", {})
    latest = {}
    counts = {}
    for d in base.get("deals", []):
        for field in ("buyer", "seller_id", "target"):
            cid = d.get(field)
            if not cid or cid not in companies:
                continue
            date = str(d.get("date") or "")
            if cid not in latest or date > latest[cid]:
                latest[cid] = date
            counts[cid] = counts.get(cid, 0) + 1
    rows = []
    for cid, date in latest.items():
        if cid in registry_idx or cid in exclude:
            continue
        profile = companies.get(cid) or {}
        if profile.get("lot"):
            continue  # лот из нескольких юрлиц — искать по имени одним юрлицом бессмысленно
        rows.append((cid, profile.get("name") or cid, date, counts.get(cid, 0)))
    rows.sort(key=lambda r: (r[2], r[3]), reverse=True)
    return rows


def attempt_single_exact_match(client, name):
    """(inn, легальное_имя) при единственном действующем точном совпадении
    имени (без формы собственности и кавычек) — иначе None. Один живой
    запрос `search` на компанию."""
    from fns_client import ApiFnsError, normalize_search_results
    from pipeline.sync_fns import norm_name

    query = clean_query_name(name)
    if not query:
        return None
    try:
        rows = normalize_search_results(client.search(query))
    except ApiFnsError:
        return None
    target = norm_name(query)
    active = [r for r in rows if "действ" in str(r.get("status") or "").lower()]
    exact = [r for r in active
             if norm_name(r.get("legal_name")) == target or norm_name(r.get("short_name")) == target]
    if len(exact) == 1 and r_inn(exact[0]):
        return exact[0]["inn"], exact[0].get("legal_name")
    return None


def r_inn(row):
    return str(row.get("inn") or "").strip() or None


def format_queue_line(cid, name, date):
    return "• %s — #/companies/%s (сделка от %s)" % (name, cid, date or "?")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--attempt", action="store_true",
                        help="живой поиск ФНС для каждой компании очереди")
    parser.add_argument("--write", action="store_true",
                        help="с --attempt: дописать однозначные находки в fns_registry.py")
    args = parser.parse_args()

    base = json.load(open(DATA, encoding="utf-8"))
    registry_idx = by_company_id()
    rows = unresolved_companies(base, registry_idx)[: args.limit]
    print("Неразрешённых кандидатов всего: %d (показаны первые %d по свежести сделки)"
         % (len(unresolved_companies(base, registry_idx)), len(rows)))
    if not rows:
        return

    if not args.attempt:
        for cid, name, date, count in rows:
            print(format_queue_line(cid, name, date))
        return

    from fns_client import ApiFnsClient

    confirmed, queue = [], []
    with ApiFnsClient() as client:
        for cid, name, date, count in rows:
            hit = attempt_single_exact_match(client, name)
            if hit:
                confirmed.append((cid, name, hit[0], hit[1]))
            else:
                queue.append((cid, name, date))
            time.sleep(0.15)

    if confirmed:
        print("Автоподтверждено (единственное точное совпадение): %d" % len(confirmed))
        for cid, name, inn, legal_name in confirmed:
            print("  %s (%s) -> ИНН %s, %s" % (name, cid, inn, legal_name))
        if args.write:
            _append_registry(confirmed)
            print("Записано в pipeline/fns_registry.py.")

    if queue:
        print("\n⚠️ Нужен ИНН вручную (%d):" % len(queue))
        for cid, name, date in queue:
            print(format_queue_line(cid, name, date))


def _append_registry(confirmed, path=None):
    from datetime import date as _date

    path = path or os.path.join(ROOT, "pipeline", "fns_registry.py")
    src = open(path, encoding="utf-8").read()
    today = os.environ.get("FNS_QUEUE_DATE") or _date.today().isoformat()
    lines = [
        "",
        "",
        "# ============================================================================",
        "# Приток — %s. Автоподтверждение pipeline/fns_unresolved_queue.py: "
        "единственное" % today,
        "# действующее юрлицо с точным именем (без формы собственности), найденное "
        "поиском",
        "# для стороны свежей сделки. Остаток того же прогона (неоднозначные "
        "случаи) —",
        "# в очереди владельцу, не угадывается.",
        "# ============================================================================",
        "REGISTRY += [",
    ]
    for cid, name, inn, legal_name in confirmed:
        reason = ("Приток, автоподтверждение: единственный действующий результат "
                  "поиска «%s», точное совпадение имени без формы собственности "
                  "(%s)." % (name.replace('"', "'"), legal_name.replace('"', "'") if legal_name else ""))
        lines.append('    {"company_id": %r, "decision": "confirmed", "inn": %r,' % (cid, inn))
        lines.append('     "reason": %r,' % reason)
        lines.append('     "date": %r},' % today)
    lines.append("]")
    marker = "\n\ndef by_company_id() -> dict[str, dict]:"
    assert marker in src, "не нашли конец REGISTRY в fns_registry.py — формат файла изменился"
    new_src = src.replace(marker, "\n".join(lines) + marker, 1)
    open(path, "w", encoding="utf-8").write(new_src)


if __name__ == "__main__":
    main()
