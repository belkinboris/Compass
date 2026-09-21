# -*- coding: utf-8 -*-
"""Очередь аудита: FALSE_PLACEHOLDER + PROFILE_DESC_IS_EVENT — первая
партия, разобрана 5 параллельными читателями (101 находка: 25
FALSE_PLACEHOLDER + 76 PROFILE_DESC_IS_EVENT, 105 уникальных ключей — 2
дубля внутри партий, плюс несколько находок дали пару связанных правок
«-b»). Итог: 97 fix (95 уникальных), 4 not_wrong, 6 defer.

Та же дисциплина, что у второй партии FIELD_MISPLACED: читатель даёт
ПОЛНЫЙ текст поля до/после, а не цитату — скрипт только сверяет текущее
поле с ожидаемым «до» перед записью. PROFILE_DESC_IS_EVENT правит только
`companies[id].desc` — это поле НЕ входит в таблицу решений читателя
review.py (та таблица — про поля сделок), поэтому у этого класса почти
не было конфликтов с блокировкой, в отличие от FIELD_MISPLACED, где
почти 90% находок пришлись на уже решённые читателем поля сделок (см.
CLAUDE.md).

Источник решений — консолидированные `out_0.json`..`out_4.json`
(`data/inbox/audit2/placeholder_profile_out/`, не в git).

    python3 pipeline/fix_audit_placeholder_profile_batch1_2026_09_21.py
    python3 pipeline/fix_audit_placeholder_profile_batch1_2026_09_21.py --write
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "static" / "data" / "deals_promoted.json"
OUT_DIR = ROOT / "data" / "inbox" / "audit2" / "placeholder_profile_out"
sys.path.insert(0, str(ROOT))

from pipeline import audit_queue as aq  # noqa: E402
from pipeline.fix_audit_move_utils import get_field, set_field  # noqa: E402


def resolve(card: dict, companies: dict, field: str):
    if field.startswith("company:"):
        rest = field[len("company:"):]
        cid, sub = rest.split(".", 1)
        if cid not in companies:
            return ("company-missing", None, None)
        return ("company", companies[cid], sub)
    return ("deal", card, field)


def main(write: bool) -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    cards = {d["id"]: d for d in data["deals"]}
    companies = data["companies"]
    decided = aq.decided_by_a_reader()

    by_key = {}
    for path in sorted(glob.glob(str(OUT_DIR / "out_*.json"))):
        for it in json.loads(Path(path).read_text(encoding="utf-8")):
            by_key.setdefault(it["key"], it)

    log: list = []
    applied = 0
    skipped = 0

    for key, it in by_key.items():
        if it["action"] != "fix":
            continue
        cid = it["card_id"]
        card = cards.get(cid)
        if card is None:
            log.append("%s (%s): карточки нет — пропущено" % (key, cid))
            skipped += 1
            continue

        field = it.get("field")
        kind, obj, sub = resolve(card, companies, field)
        if kind == "company-missing":
            log.append("%s (%s): компания не найдена — пропущено" % (key, cid))
            skipped += 1
            continue
        if kind == "deal" and (cid, sub) in decided:
            log.append("%s (%s): %s решено читателем review.py — пропущено" % (key, cid, sub))
            skipped += 1
            continue

        cur = obj.get(sub) if kind == "company" else (get_field(card, sub) if "." in sub else card.get(sub))
        expected_old = it.get("old_full_text")
        if expected_old is not None and (cur or "") != expected_old:
            log.append("%s (%s): %s не совпадает с ожидаемым — пропущено" % (key, cid, sub))
            skipped += 1
            continue

        new_val = it.get("new_full_text")
        log.append("%s (%s): %s обновлено" % (key, cid, field))
        applied += 1
        if write:
            if kind == "company":
                obj[sub] = new_val
            elif "." in sub:
                set_field(card, sub, new_val)
            else:
                card[sub] = new_val

    print("Применено: %d, пропущено: %d" % (applied, skipped))
    for line in log:
        print("   " + line)

    if not write:
        print("\n(сухой прогон; чтобы записать — --write)")
        return 0
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nзаписано")
    return 0


if __name__ == "__main__":
    sys.exit(main("--write" in sys.argv))
