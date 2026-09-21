# -*- coding: utf-8 -*-
"""Закрытие очереди аудита: смешанная партия из семнадцати классов.

Партия собрана не по классу, а по признаку «это можно внести, прочитав
карточку»: ROLE_MISSING (сторона названа в тексте, но поля роли нет),
OTHER, TYPE_MISMATCH, SUM_FIELDS_DIFFER, CONTRADICTION, SUM_NOT_PRICE,
STATUS_MISMATCH, DATE_MISMATCH, ASSET_IS_DESCRIPTION, PARTY_IN_ASSET_NAME,
FALSE_PLACEHOLDER, TRUNCATED и другие мелкие.

За её границами осталось то, что прочтением одной карточки не закрывается,
и это названо честно, а не отложено молча:
  • UNLINKED_PARTY (536) — сторона названа текстом, профиля компании в базе
    нет. Механический путь исчерпан: `link_parties.py` находит ровно одну
    привязку на всю базу. Разных названий за находками — 497, то есть это
    кампания заведения профилей, а не партия правок.
  • FIELD_MISPLACED (349) — из них 252 упираются в поле, которое уже писал
    читатель через review.py. Перенести текст ИЗ такого поля значит оставить
    строку таблицы правок неприменённой и уронить
    `test_review_table_is_applied_and_not_pending`. Механизм «правка
    применена, хотя поле изменилось» в проекте есть (`proofread_absorbed`),
    но он про вычитку; распространять его на переносы — отдельное решение.

ДИСЦИПЛИНА ПРИМЕНЕНИЯ — та же, что у предыдущих партий, и каждая её часть
появилась после конкретной поломки:
 1. Читатель отдаёт ПОЛНЫЙ текст поля до и после; скрипт сверяет «до» с
    текущим значением и молча не пишет ничего, если оно разошлось.
 2. Машинная правка не спорит с прочитанным: поле, по которому читатель уже
    принял решение через review.py, пропускается.
 3. Ссылка на профиль принимается только на существующий id — иначе это
    выдумка.
 4. Одна компания — одна роль в сделке; карточка, где после правок это
    нарушилось бы, откатывается целиком.
 5. Несколько правок одной находки применяются В ПОРЯДКЕ, который дал
    читатель (сначала снятие ссылки, потом установка), иначе на мгновение
    возникает запрещённое состояние.

    python3 pipeline/fix_audit_close_2026_09_21.py
    python3 pipeline/fix_audit_close_2026_09_21.py --write
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
OUT_DIR = ROOT / "data" / "inbox" / "audit2" / "close_out"
sys.path.insert(0, str(ROOT))

from pipeline import audit_queue as aq  # noqa: E402
from pipeline.fix_audit_move_utils import get_field, set_field  # noqa: E402

sys.path.insert(0, str(ROOT / "pipeline" / "ingest"))
from review import _linker_key  # noqa: E402  «ООО «Х»» и «Х» — одно имя

ROLE_IDS = ("buyer", "seller_id", "target", "asset_id")
SRC_RX = re.compile(r"^src\[(\d+)\]\[(\d+)\]$")
ADV_RX = re.compile(r"^law\.adv\[(\d+)\]\[(\d+)\]$")
EVENT_RX = re.compile(r"^events\[(\d+)\]\.(\w+)$")
AS_JSON = ("law.adv", "events", "src")
STRAIGHT_QUOTES = ('"', "“", "”")
QUOTED_FIELDS = ("title", "seller", "buyer_name", "asset")


def read_field(card, companies, field):
    """(текущее значение, функция записи) или (None, None), если поля нет."""
    if field.startswith("company:"):
        cid, sub = field[len("company:"):].split(".", 1)
        comp = companies.get(cid)
        if comp is None:
            return None, None
        return comp.get(sub), lambda v: comp.__setitem__(sub, v)
    for rx, getter in ((SRC_RX, "src"), (ADV_RX, "adv")):
        m = rx.match(field)
        if m:
            i, j = int(m.group(1)), int(m.group(2))
            box = (card.get("src") or []) if getter == "src" else ((card.get("law") or {}).get("adv") or [])
            if i >= len(box) or j >= len(box[i]):
                return None, None
            return box[i][j], lambda v: box[i].__setitem__(j, v)
    m = EVENT_RX.match(field)
    if m:
        i, sub = int(m.group(1)), m.group(2)
        events = card.get("events") or []
        if i >= len(events):
            return None, None
        return events[i].get(sub), lambda v: events[i].__setitem__(sub, v)
    cur = get_field(card, field) if "." in field else card.get(field)
    setter = ((lambda v: set_field(card, field, v)) if "." in field
              else (lambda v: card.__setitem__(field, v)))
    if field in AS_JSON:
        return json.dumps(cur, ensure_ascii=False), lambda v: setter(
            json.loads(v) if isinstance(v, str) else v)
    return cur, setter


def roles_are_distinct(card):
    used = [card.get(r) for r in ROLE_IDS if card.get(r)]
    return len(used) == len(set(used))


def main(write: bool, out_dir=None) -> int:
    global OUT_DIR
    if out_dir:
        OUT_DIR = ROOT / "data" / "inbox" / "audit2" / out_dir
    data = json.loads(DATA.read_text(encoding="utf-8"))
    cards = {d["id"]: d for d in data["deals"]}
    companies = data["companies"]
    decided = aq.decided_by_a_reader()

    items = []
    for path in sorted(glob.glob(str(OUT_DIR / "out_*.json"))):
        for it in json.loads(Path(path).read_text(encoding="utf-8")):
            if it.get("action") == "fix":
                items.append(it)
    # ГРУППИРУЕМ ПО НАХОДКЕ, А НЕ ПО КАРТОЧКЕ. Первая версия откатывала всю
    # карточку при первом несовпадении «до» — и уносила с собой правки других
    # читателей по той же карточке: у `g4cd1fa52` устаревшее «до» в одном
    # файле отменяло верную правку из другого. Единица отката — находка
    # (`key`): её правки применяются все или ни одной (они бывают связаны:
    # «снять ссылку» + «поставить другую»), а соседние находки не страдают.
    by_key = {}
    for it in items:
        by_key.setdefault((it["card_id"], it["key"]), []).append(it)

    log, applied, skipped = [], 0, 0
    for (cid, _key), parts in by_key.items():
        card = cards.get(cid)
        if card is None:
            log.append("%s: карточки нет — пропущено (%d)" % (cid, len(parts)))
            skipped += len(parts)
            continue
        before = copy.deepcopy(card)
        trouble, done = None, []
        for it in parts:
            field = str(it.get("field") or "")
            new = it.get("new_full_text")
            if not field:
                trouble = "правка без поля"
                break
            if not field.startswith("company:") and (cid, field) in decided:
                trouble = "%s решено читателем review.py" % field
                break
            if field in ROLE_IDS and new and new not in companies:
                trouble = "профиля %s нет в базе — это была бы выдумка" % new
                break
            if field in QUOTED_FIELDS and isinstance(new, str) \
                    and any(q in new for q in STRAIGHT_QUOTES):
                trouble = "в %s кавычки не ёлочки" % field
                break
            cur, setter = read_field(card, companies, field)
            if setter is None:
                trouble = "поле %s не разрешилось" % field
                break
            expected = it.get("old_full_text")
            if not ((cur or None) == (expected or None) or str(cur) == str(expected)):
                trouble = "%s не совпадает с ожидаемым «до»" % field
                break
            setter(new)
            done.append(field)
        # ПОКУПАТЕЛЬ НАЗВАН ОДИН РАЗ — профилем ИЛИ текстом (замер: 1096
        # карточек только с профилем, 155 только с текстом, ни одной с
        # обоими; держит `test_buyer_is_named_once`). У продавца соглашение
        # ДРУГОЕ: и профиль, и текст стоят у 316 карточек — там чистить
        # нечего. Привязка покупателя обязана убрать текст, но убрать его
        # можно не всегда:
        #   • текст писал читатель через review.py и имя профиля с ним не
        #     совпадает — снятие оставит строку таблицы правок неприменённой
        #     («Группа компаний «Свеза»» против профиля «Свеза»);
        #   • в тексте названы ДВЕ стороны («X и Y») — одной ссылкой это не
        #     выражается, и половина факта пропадёт.
        # В обоих случаях привязка откатывается, находка уходит владельцу:
        # пустое место честнее половины факта.
        if not trouble and card.get("buyer") and card.get("buyer_name") \
                and any(p.get("field") == "buyer" for p in parts):
            name = (companies.get(card["buyer"]) or {}).get("name") or ""
            text = str(card.get("buyer_name") or "")
            if (cid, "buyer_name") in decided and _linker_key(name) != _linker_key(text):
                trouble = "имя покупателя текстом поставил читатель и оно шире профиля"
            elif re.search(r"\sи\s|,", text):
                trouble = "в тексте названы две стороны — одной ссылкой не выражается"
            else:
                card.pop("buyer_name", None)
                done.append("buyer_name снято (имя несёт профиль)")
        # Флаг «предметом стоял продавец» — пометка о ДЕФЕКТЕ, а не факт
        # сделки: клиент по нему выводит сноску «подробности о предмете — во
        # вкладке «Экономист»». Как только предмет привязан, пометка врёт о
        # состоянии карточки. Снимается тем же движением, что и в
        # `merge_essity_shilov_dup.py`.
        if not trouble and card.get("target") and card.get("target_was_seller") \
                and any(p.get("field") == "target" for p in parts):
            card.pop("target_was_seller", None)
            done.append("target_was_seller снят (предмет привязан)")
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

    print("Применено правок: %d, пропущено: %d" % (applied, skipped))
    for line in log:
        print("   " + line)
    if not write:
        print("\n(сухой прогон; чтобы записать — --write)")
        return 0
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nзаписано")
    return 0


if __name__ == "__main__":
    d = None
    for i, a in enumerate(sys.argv):
        if a == "--dir" and i + 1 < len(sys.argv):
            d = sys.argv[i + 1]
    sys.exit(main("--write" in sys.argv, d))
