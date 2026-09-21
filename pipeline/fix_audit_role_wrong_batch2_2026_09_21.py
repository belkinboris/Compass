# -*- coding: utf-8 -*-
"""Очередь аудита: роль стороны названа неверно — вторая партия (48 находок).

Что такое ROLE_WRONG: продавцом назван предмет сделки, покупателем — группа
вместо конкретного юрлица, предметом — материнская компания вместо купленной
«дочки». Для сайта это не мелочь: сделка на 320 млрд ₽ висит на странице не
той компании, а слой фактов берёт ИНН чужого юрлица и считает предмет
подтверждённым — так у «Роснефть — Артаг» знаменатель приходил от
материнской «Роснефти», а не от покупаемой компании.

Пять читателей разобрали 42 находки, свободные от замка «машинная правка не
спорит с прочитанным»: 24 правки, 4 находки не подтвердились, 20 требуют
решения владельца (нужен профиль компании, которого в базе нет, — выдумывать
его читателю запрещено, пустое поле честнее неверной ссылки).

ТРИ ВЕЩИ, О КОТОРЫЕ ЭТА ПАРТИЯ СПОТЫКАЛАСЬ БЫ БЕЗ ЗАЩИТЫ.

1. ПОРЯДОК ВНУТРИ ОДНОЙ НАХОДКИ. Четыре находки чинятся несколькими полями
   сразу («снять ссылку из buyer» + «поставить её же в target»). Если
   применить их в обратном порядке, компания на мгновение окажется в двух
   ролях и упадёт `test_one_company_holds_one_role_in_a_deal`. Поэтому
   записи одного ключа применяются строго в том порядке, в каком их дал
   читатель, а файлы читаются по именам — детерминированно.

2. ССЫЛКА ТОЛЬКО НА СУЩЕСТВУЮЩИЙ ПРОФИЛЬ. Любой id, которого нет в
   `companies`, — отказ всей правки: именно так выглядела бы выдумка.

3. ОДНА КОМПАНИЯ — ОДНА РОЛЬ. После каждой карточки проверяется тот же
   инвариант, что и в тестах; нарушение откатывает карточку целиком.

    python3 pipeline/fix_audit_role_wrong_batch2_2026_09_21.py
    python3 pipeline/fix_audit_role_wrong_batch2_2026_09_21.py --write
"""
from __future__ import annotations

import copy
import glob
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "static" / "data" / "deals_promoted.json"
OUT_DIR = ROOT / "data" / "inbox" / "audit2" / "role_wrong_out2"
sys.path.insert(0, str(ROOT))

from pipeline import audit_queue as aq  # noqa: E402
from pipeline.fix_audit_move_utils import get_field, set_field  # noqa: E402

ROLE_IDS = ("buyer", "seller_id", "target", "asset_id")

# ИСКЛЮЧЕНИЕ ИЗ «МАШИННАЯ ПРАВКА НЕ СПОРИТ С ПРОЧИТАННЫМ» — узкое и
# самопроверяемое. Прежнее решение читателя по этим двум полям было СНЯТИЕМ
# неверной ссылки (`new: None`): оно говорит, кем сторона НЕ является, и не
# утверждает, что она неизвестна. Поставить верный профиль в поле, которое
# то решение оставило пустым, — не спор с ним, а его продолжение.
#
# Обобщать правило я не стал, и вот почему: по всей очереди (1258 ждущих
# находок) решением читателя заблокированы 526, и ТОЛЬКО снятием — три.
# Ради трёх ослаблять забор, который дважды поймал настоящую поломку
# («строка таблицы правок применена к базе»), невыгодно. Поэтому исключение
# перечислено поимённо, а скрипт в момент применения САМ убеждается, что
# прежнее решение было снятием и что поле сейчас пустое; если таблица FIXES
# изменится, исключение перестанет действовать, а не расширится молча.
UNBLOCKED = {
    ("ksk", "target"),         # было «cargill → None»; ставим предмет — КСК
}

# ЗДЕСЬ БЫЛО ВТОРОЕ ИСКЛЮЧЕНИЕ, И ПОЛНЫЙ PYTEST ЕГО СНЯЛ — запись оставлена,
# чтобы следующий прогон не завёл его заново. У `gff6e08fe` читатель снял
# ссылку `buyer` И ТУТ ЖЕ вписал имя текстом («buyer_name: None →
# «Сбербанк инвестиции»»). То есть решение было не «это не тот профиль», а
# «покупатель здесь называется текстом» — положительный выбор, а не отказ.
# Поставив профиль, скрипт стёр бы этот текст и сломал инвариант «строка
# таблицы правок применена к базе» (`test_review_table_is_applied_and_not_
# pending`) — тот самый, ради которого правило «машинная правка не спорит с
# прочитанным» и существует. Привязать профиль здесь можно, но через сам
# review.py, его же путём, а не в обход.
#
# Разница с `ksk` ровно в этом: там читатель снял `target` и НИЧЕГО взамен
# не написал, поле осталось пустым.


def prior_decision_was_a_removal(cid, field):
    """Прежнее решение читателя по этому полю — снятие значения, а не выбор.

    Мало проверить само поле: снятие ссылки в паре с записью имени текстом —
    это выбор, а не отказ (см. запись про `gff6e08fe` выше). Поэтому
    соседнее поле-имя тоже обязано быть нетронутым.
    """
    sys.path.insert(0, str(ROOT / "pipeline" / "ingest"))
    import review
    twin = {"buyer": "buyer_name", "seller_id": "seller",
            "target": "asset", "asset_id": "asset"}.get(field)
    prior = [f for f in review.FIXES if f["id"] == cid and f.get("field") == field]
    wrote_twin = [f for f in review.FIXES
                  if f["id"] == cid and f.get("field") == twin and f.get("new")]
    return bool(prior) and not wrote_twin and all(f.get("new") in (None, "") for f in prior)
ADV_RX = re.compile(r"^law\.adv\[(\d+)\]\[(\d+)\]$")
# Читатель отдаёт значение поля-списка как JSON-строку — так же, как в
# предыдущих партиях (law.adv, events).
AS_JSON = ("law.adv",)


def read_field(card, field):
    """(текущее значение, функция записи) или (None, None), если поля нет."""
    m = ADV_RX.match(field)
    if m:
        i, j = int(m.group(1)), int(m.group(2))
        adv = (card.get("law") or {}).get("adv") or []
        if i >= len(adv) or j >= len(adv[i]):
            return None, None
        return adv[i][j], lambda v: adv[i].__setitem__(j, v)
    if field in AS_JSON:
        cur = get_field(card, field) if "." in field else card.get(field)
        setter = ((lambda v: set_field(card, field, v)) if "." in field
                  else (lambda v: card.__setitem__(field, v)))
        return json.dumps(cur, ensure_ascii=False), lambda v: setter(
            json.loads(v) if isinstance(v, str) else v)
    cur = get_field(card, field) if "." in field else card.get(field)
    setter = ((lambda v: set_field(card, field, v)) if "." in field
              else (lambda v: card.__setitem__(field, v)))
    return cur, setter


def roles_are_distinct(card):
    """Одна компания не занимает в сделке две роли."""
    used = [card.get(r) for r in ROLE_IDS if card.get(r)]
    return len(used) == len(set(used))


def main(write: bool) -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    cards = {d["id"]: d for d in data["deals"]}
    companies = data["companies"]
    decided = aq.decided_by_a_reader()

    # Сохраняем порядок: сначала файл, потом позиция внутри файла.
    items = []
    for path in sorted(glob.glob(str(OUT_DIR / "out_*.json"))):
        for it in json.loads(Path(path).read_text(encoding="utf-8")):
            if it.get("action") == "fix":
                items.append(it)

    by_card = {}
    for it in items:
        by_card.setdefault(it["card_id"], []).append(it)

    log, applied, skipped = [], 0, 0
    for cid, parts in by_card.items():
        card = cards.get(cid)
        if card is None:
            log.append("%s: карточки нет — пропущено (%d правок)" % (cid, len(parts)))
            skipped += len(parts)
            continue
        before = copy.deepcopy(card)
        trouble, done = None, []
        for it in parts:
            field = it.get("field") or ""
            if (cid, field) in decided:
                cur_now, _ = read_field(card, field)
                if not ((cid, field) in UNBLOCKED
                        and prior_decision_was_a_removal(cid, field)
                        and not cur_now):
                    trouble = "%s решено читателем review.py" % field
                    break
                log.append("   %s/%s: прежнее решение было снятием ссылки, "
                           "поле пусто — заполняем" % (cid, field))
            new = it.get("new_full_text")
            if field in ROLE_IDS and new and new not in companies:
                trouble = "профиля %s нет в базе — это была бы выдумка" % new
                break
            cur, setter = read_field(card, field)
            if setter is None:
                trouble = "поле %s не разрешилось" % field
                break
            expected = it.get("old_full_text")
            # Читатель пишет отсутствующее значение как None или "None".
            same = (cur or None) == (expected or None) or str(cur) == str(expected)
            if not same:
                trouble = "%s не совпадает с ожидаемым «до»" % field
                break
            setter(new)
            done.append(field)
        # ПОКУПАТЕЛЬ НАЗВАН ОДИН РАЗ — профилем ИЛИ текстом, не обоими сразу
        # (замер: 1096 карточек только с профилем, 155 только с текстом, ни
        # одной с обоими; держит `test_buyer_is_named_once`). У ПРОДАВЦА это
        # НЕ так: и профиль, и текст стоят у 316 карточек — там соглашение
        # другое, и чистить его было бы порчей данных. Один и тот же на вид
        # приём оказался верным для одного поля и неверным для соседнего —
        # поэтому мерить пришлось оба, а не распространять правило по
        # аналогии.
        if not trouble and card.get("buyer") and card.get("buyer_name") \
                and any(p.get("field") == "buyer" for p in parts):
            if (cid, "buyer_name") in decided:
                trouble = "имя покупателя текстом поставил читатель — профиль здесь через review.py"
            else:
                card.pop("buyer_name", None)
                done.append("buyer_name снято (имя несёт профиль)")
        if not trouble and not roles_are_distinct(card):
            trouble = "после правки компания заняла бы две роли"
        if trouble:
            cards[cid].clear()
            cards[cid].update(before)
            log.append("%s: %s — откат %d правок" % (cid, trouble, len(parts)))
            skipped += len(parts)
            continue
        log.append("%s: %s" % (cid, ", ".join(done)))
        applied += len(done)

    print("Применено правок: %d, пропущено: %d (карточек тронуто: %d)"
          % (applied, skipped, sum(1 for line in log if "—" not in line)))
    for line in log:
        print("   " + line)
    if not write:
        print("\n(сухой прогон; чтобы записать — --write)")
        return 0
    # Заменяем список сделок на месте: cards хранит те же объекты.
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nзаписано")
    return 0


if __name__ == "__main__":
    sys.exit(main("--write" in sys.argv))
