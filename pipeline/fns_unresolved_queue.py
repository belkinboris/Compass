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

ДОСТАВКА В КОНСОЛЬ (этап 3, П3'''). Раньше остаток печатался в stdout
одноразового контейнера — никто не видел («очередь, которая падает в
одноразовый контейнер, — не очередь», урок CLAUDE.md). `--to-console --write`
шлёт остаток (после `--attempt`, если он был; без него — весь список) в
ту же Telegram-консоль, что и черновики (`send_targets()`/`send_one()` из
`pipeline/ingest/send_drafts.py`), по одному сообщению на компанию, с
маркером `[инн <id>]` в первой строке. Ответ владельца текстом (номер ИНН)
приходит вебхуком как ЗАМЕТКА с `deal_id = "инн~<id>"` (main.py,
`telegram_webhook`) — префикс защищает от совпадения с id сделки (7 таких
совпадений уже есть в базе, кураторские слаги вроде `citibank`). Заметку
разбирает `pipeline/fns_notes_to_registry.py`.

ПОЧЕМУ КОМПАНИЯ НЕ СПРАШИВАЕТСЯ ДВАЖДЫ. Отправка ставит `company["fns_asked"]
= <дата>` прямо на профиль в `deals_promoted.json` (тот же приём, что
`reviewed`/`deep_researched` на карточках сделок, — штамп пережил бы
контейнер, потому что он в git). `unresolved_companies()` пропускает
профили со штампом — иначе владелец видел бы одну и ту же компанию каждый
день, пока не ответит. Обратная сторона: если ответ так и не пришёл, компания
не вернётся в очередь сама — перепрос по расписанию не сделан, это заведомый
компромисс, не забытая часть.

Запуск:
    python3 pipeline/fns_unresolved_queue.py            # список, без сети
    python3 pipeline/fns_unresolved_queue.py --limit 20 --attempt --write
        # первые 20 по свежести: попытка автоподтверждения (живой поиск),
        # подтверждённое пишется в pipeline/fns_registry.py, остальное —
        # готовый текст для консоли
    python3 pipeline/fns_unresolved_queue.py --limit 20 --attempt --to-console --write
        # то же самое, плюс отправка неразрешённого остатка в консоль
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

# Профили, у которых заподозрено, что это карточка-близнец другого
# профиля, — решать ФНС-сопоставлением для них нельзя, пока не сверены и
# не слиты (история с «Mail»/«VK»: один ИНН, найденный поиском, оказался
# уже подтверждён другому профилю — тест не пропустил бы задвоение).
# 23 августа 2026 четыре найденные кампанией пары (Лента/«Группа Лента»,
# банк «Открытие»/«ФК Открытие», «Аптечная сеть 36,6»/«Аптечная группа
# «36,6»», Mail/VK) слиты pipeline/merge_company_twins_fns_campaign.py —
# множество снова пусто, до следующей находки.
SUSPECTED_TWIN_PROFILES = set()

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
        if profile.get("fns_asked"):
            continue  # уже спросили в консоли (штамп даты) — не повторять молчащий вопрос
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


# Сколько компаний слать в консоль за прогон. «10-15 строк» из брифа — то же
# по духу ограничение, что RAW_PER_RUN в send_drafts.py: без предела очередь
# из полусотни компаний легла бы одним разом и стала бы шумом, который
# перестают читать (тот же урок CLAUDE.md, «консоль, куда валят всё»).
CONSOLE_PER_RUN = 15

SITE = os.environ.get("APP_BASE_URL", "https://projectcompass.ru").rstrip("/")


def console_message(cid, name, date):
    """⚠️ [инн <id>] — маркер, который main.py::telegram_webhook разбирает
    как ответ-заметку с deal_id="инн~<id>" (см. докстринг модуля)."""
    return ("⚠️ [инн %s] — НУЖЕН ИНН\n"
            "%s\n"
            "Карточка: %s/#/companies/%s\n"
            "Сделка от %s\n\n"
            "Ответьте номером ИНН (10 или 12 цифр) — впишем в реестр "
            "pipeline/fns_registry.py после проверки контрольной суммы."
            % (cid, name, SITE, cid, date or "?"))


def send_queue_to_console(queue, write):
    """Отправить остаток очереди в Telegram-консоль, по одному сообщению на
    компанию (без клавиатуры — решение здесь не кнопка, а текстовый ответ).
    write=False — только план, ничего не уходит и штамп не ставится."""
    HERE = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(HERE, "ingest"))
    import send_drafts
    import telegram_endpoint

    batch = queue[:CONSOLE_PER_RUN]
    targets = send_drafts.send_targets()
    if not targets:
        print("Ни TELEGRAM_REVIEW_GROUP_ID, ни TELEGRAM_REVIEW_CHAT_IDS не заданы — "
              "консоли нет, остаток не отправлен.")
        return []
    if not write:
        print("\nВ консоль ушло бы %d сообщений (сухой прогон — не отправлено):" % len(batch))
        for cid, name, date in batch:
            print(format_queue_line(cid, name, date))
        return []

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        print("TELEGRAM_BOT_TOKEN не задан — консоли нет, остаток не отправлен.")
        return []

    import httpx
    sent = []
    with httpx.Client(timeout=20) as client:
        for cid, name, date in batch:
            text = console_message(cid, name, date)
            ok = all(send_drafts.send_one(client, token, chat, text, None) for chat in targets)
            if ok:
                sent.append(cid)
            time.sleep(send_drafts.PAUSE)
    print("В консоль отправлено: %d" % len(sent))
    return sent


def stamp_asked(base, cids, path=None):
    """Штамп `fns_asked` прямо на профиль — тот же приём, что `reviewed` на
    карточке сделки: переживает контейнер, потому что в git, и не даёт
    unresolved_companies() спросить о той же компании завтра снова."""
    from datetime import date as _date

    path = path or DATA
    today = os.environ.get("FNS_QUEUE_DATE") or _date.today().isoformat()
    comps = base["companies"]
    for cid in cids:
        if cid in comps:
            comps[cid]["fns_asked"] = today
    with open(path, "w", encoding="utf-8") as f:
        json.dump(base, f, indent=1, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--attempt", action="store_true",
                        help="живой поиск ФНС для каждой компании очереди")
    parser.add_argument("--to-console", action="store_true",
                        help="отправить неразрешённый остаток в Telegram-консоль")
    parser.add_argument("--write", action="store_true",
                        help="с --attempt: дописать находки в fns_registry.py; "
                             "с --to-console: реально отправить и проставить fns_asked")
    args = parser.parse_args()

    # ИТОГ ПРОГОНА (28 августа, П1-11) — печатается ВСЕГДА, одной строкой, и
    # обязан попасть в коммит-сообщение рутины (шаг 6 её промпта требует
    # называть эти числа). Триггер пять прогонов подряд не оставил следа
    # (0 fns_asked, 0 коммитов) при непустой очереди 1013 кандидатов — а
    # обычные "print" внутри условий легко потерять в выводе модели,
    # пересказывающей прогон своими словами. Эта строка — не пересказ,
    # три голых числа, специально ради того, чтобы тихий провал стало
    # физически не с чем спутать.
    confirmed_n = sent_n = 0

    base = json.load(open(DATA, encoding="utf-8"))
    registry_idx = by_company_id()
    rows = unresolved_companies(base, registry_idx)[: args.limit]
    total_unresolved = len(unresolved_companies(base, registry_idx))
    print("Неразрешённых кандидатов всего: %d (показаны первые %d по свежести сделки)"
         % (total_unresolved, len(rows)))
    if not rows:
        print("ИТОГ ПРОГОНА: очередь пуста, отправлять некому (confirmed=0, отправлено=0).")
        return

    if not args.attempt:
        queue = [(cid, name, date) for cid, name, date, count in rows]
    else:
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
                confirmed_n = len(confirmed)
                print("Записано в pipeline/fns_registry.py.")

    if queue:
        print("\n⚠️ Нужен ИНН вручную (%d):" % len(queue))
        for cid, name, date in queue:
            print(format_queue_line(cid, name, date))

    if args.to_console and queue:
        sent = send_queue_to_console(queue, args.write)
        if sent:
            stamp_asked(base, sent)
            sent_n = len(sent)
            print("Проставлен fns_asked профилям: %d" % sent_n)

    print("ИТОГ ПРОГОНА: неразрешённых кандидатов %d, автоподтверждено %d, "
          "отправлено в консоль %d." % (total_unresolved, confirmed_n, sent_n))


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
