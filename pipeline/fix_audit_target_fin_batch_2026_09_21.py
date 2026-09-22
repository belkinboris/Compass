# -*- coding: utf-8 -*-
"""«Финансы покупаемой компании» (eco.target_fin) несёт оценки и мотивы —
партия по eco.target_fin (аудит 13 сентября). Из 11 находок этого поля,
свободных от чтения по источнику, 2 (`c460a1f82`, `g92107ce6`, `g3c46e216`
— три карточки) упираются в занятое назначение (eco.val/eco.context
решены читателем). Здесь — оставшиеся 6 карточек (7 находок, у
`g432502a3` их две с одинаковым смыслом).

    python3 pipeline/fix_audit_target_fin_batch_2026_09_21.py
    python3 pipeline/fix_audit_target_fin_batch_2026_09_21.py --write
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "static" / "data" / "deals_promoted.json"
sys.path.insert(0, str(ROOT))

from pipeline import audit_queue as aq  # noqa: E402
from pipeline.fix_audit_move_utils import apply_move, get_field, set_field  # noqa: E402

WHOLE_MOVES = [
    # (id, поле-назначение) — весь текст target_fin не о предмете.
    ("cc16fce80", "eco.val"),
    ("gfd5e2810", "eco.val"),
    ("ektos", "extra"),
    ("g432502a3", "eco.val"),
    ("g66cb145a", "eco.rationale"),
]

# gcd2b0954: extra→target_fin (поле пусто), а не наоборот.
FILL_ID = "gcd2b0954"
FILL_QUOTE = ("включая ООО «Банк Точка» с капиталом 7,36 млрд ₽; на 1 июня "
              "2023 года совокупные балансовые активы банка составляли "
              "188,9 млрд ₽")

# g489b4309: одно предложение несёт И оценку суммы сделки (eco.val), И
# цифры о самом предмете (target_fin) — переписывается на два отдельных
# предложения по тем же фактам, без выдумки.
SPLIT_ID = "g489b4309"
SPLIT_OLD = ("Сумма сделки сторонами не раскрывается; по неофициальной "
             "оценке, она составляет несколько миллиардов рублей исходя "
             "из выручки ВКТ в 3,6 млрд ₽ по итогам 2025 года (при этом "
             "выручка снизилась год к году на 8%, а чистая прибыль — на "
             "35%, до 15,8 млн ₽).")
SPLIT_NEW_VAL = ("Сумма сделки сторонами не раскрывается; по неофициальной "
                  "оценке, она составляет несколько миллиардов рублей "
                  "исходя из выручки ВКТ.")
SPLIT_NEW_TARGET_FIN = ("Выручка ВКТ по итогам 2025 года — 3,6 млрд ₽ "
                        "(-8% год к году), чистая прибыль снизилась на "
                        "35%, до 15,8 млн ₽.")


def main(write: bool) -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    cards = {d["id"]: d for d in data["deals"]}
    decided = aq.decided_by_a_reader()
    log: list = []

    for cid, dst in WHOLE_MOVES:
        card = cards[cid]
        full = get_field(card, "eco.target_fin") or ""
        apply_move(card, "eco.target_fin", full, dst, write, decided, cid, log)

    fill = cards[FILL_ID]
    apply_move(fill, "extra", FILL_QUOTE, "eco.target_fin", write, decided, FILL_ID, log)

    split = cards[SPLIT_ID]
    cur = get_field(split, "eco.target_fin")
    if cur != SPLIT_OLD:
        log.append("%s: eco.target_fin не совпало — пропущено" % SPLIT_ID)
    elif (SPLIT_ID, "eco.target_fin") in decided or (SPLIT_ID, "eco.val") in decided:
        log.append("%s: eco.target_fin или eco.val решены читателем — пропущено" % SPLIT_ID)
    else:
        val = get_field(split, "eco.val") or ""
        new_val = SPLIT_NEW_VAL if not val or val in ("—", "-") else val + " " + SPLIT_NEW_VAL
        log.append("%s: target_fin переписан на два предложения — оценка суммы в eco.val, финансы ВКТ остаются" % SPLIT_ID)
        if write:
            set_field(split, "eco.val", new_val)
            set_field(split, "eco.target_fin", SPLIT_NEW_TARGET_FIN)

    print("Записей: %d" % len(log))
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
