# -*- coding: utf-8 -*-
"""«Цель сделки» (eco.rationale) несёт предположения о покупателе, описание
продукта, дубли уже сказанного и механику финансирования — партия по
eco.rationale (аудит 13 сентября). Из 10 находок этого поля, свободных от
чтения по источнику, 3 упираются в занятое назначение (eco.context решено
читателем); здесь — оставшиеся 7.

    python3 pipeline/fix_audit_rationale_batch_2026_09_21.py
    python3 pipeline/fix_audit_rationale_batch_2026_09_21.py --write
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "static" / "data" / "deals_promoted.json"
sys.path.insert(0, str(ROOT))

from pipeline import audit_queue as aq  # noqa: E402
from pipeline.fix_audit_move_utils import apply_move, get_field, set_field  # noqa: E402

WHOLE_MOVES = [
    # (id, поле-назначение) — весь текст eco.rationale не о мотиве.
    ("g672dcca1", "eco.context"),
    ("gafe121ae", "eco.context"),
    ("g62698716", "law.struct"),
]

SENTENCE_MOVES = [
    # (id, цитата, назначение) — часть поля.
    ("g17fc21d6",
     "По неофициальным данным, переговоры находились на заключительной "
     "стадии, а претендентов на актив было два.",
     "eco.context"),
]

# g8b03762d: описание ПРОДУКТА (что делает платформа) переезжает в
# eco.share, а не в context — план основателя по использованию денег и
# задача компании остаются законным мотивом.
PRODUCT_ID = "g8b03762d"
PRODUCT_QUOTE = (
    "Стартап разработал ИИ-платформу для ресторанов, отелей и "
    "туристической отрасли. Она автоматизирует весь путь гостя — от "
    "первого обращения до бронирования и оплаты — и объединяет "
    "ИИ-ресепшн, онлайн-бронирование с оплатой, инструменты привлечения "
    "гостей через партнёрские каналы и мобильный гастронавигатор. "
    "Продукт интегрируется с отраслевыми системами, включая iiko и Bnovo."
)

# gf6232eec: перефразированный дубль уже точного факта в eco.fin — просто
# снимается, без переноса.
DUP_ID = "gf6232eec"
DUP_OLD = "Сделка обеспечила единовременное поступление 14,8 млрд ₽ в бюджет Республики Башкортостан."

# g0201b97a: почти всё поле — редундантный пересказ уже структурированных
# полей карточки (дата закрытия, стороны — они и так на карточке отдельно);
# единственный самостоятельный факт («переговоры велись несколько
# месяцев») переносится в context, остальное честно снимается.
NEGOT_ID = "g0201b97a"
NEGOT_OLD = ("Сделка закрыта 25 февраля 2025 года. «Ингосстрах» продал "
             "100% акций АО «Ингосстрах Банк» холдингу «Авторитэйл». "
             "Переговоры велись несколько месяцев.")
NEGOT_KEEP_FACT = "Переговоры велись несколько месяцев."


def main(write: bool) -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    cards = {d["id"]: d for d in data["deals"]}
    decided = aq.decided_by_a_reader()
    log: list = []

    for cid, dst in WHOLE_MOVES:
        card = cards[cid]
        full = get_field(card, "eco.rationale") or ""
        apply_move(card, "eco.rationale", full, dst, write, decided, cid, log)

    for cid, quote, dst in SENTENCE_MOVES:
        card = cards[cid]
        apply_move(card, "eco.rationale", quote, dst, write, decided, cid, log)

    prod = cards[PRODUCT_ID]
    apply_move(prod, "eco.rationale", PRODUCT_QUOTE, "eco.share", write, decided, PRODUCT_ID, log)

    dup = cards[DUP_ID]
    cur = get_field(dup, "eco.rationale")
    if cur != DUP_OLD:
        log.append("%s: eco.rationale не совпало — пропущено" % DUP_ID)
    elif (DUP_ID, "eco.rationale") in decided:
        log.append("%s: eco.rationale решено читателем — пропущено" % DUP_ID)
    else:
        log.append("%s: eco.rationale снят (перефразированный дубль eco.fin)" % DUP_ID)
        if write:
            set_field(dup, "eco.rationale", "—")

    negot = cards[NEGOT_ID]
    cur = get_field(negot, "eco.rationale")
    if cur != NEGOT_OLD:
        log.append("%s: eco.rationale не совпало — пропущено" % NEGOT_ID)
    elif (NEGOT_ID, "eco.rationale") in decided or (NEGOT_ID, "eco.context") in decided:
        log.append("%s: eco.rationale или eco.context решены читателем — пропущено" % NEGOT_ID)
    else:
        ctx = get_field(negot, "eco.context") or ""
        new_ctx = NEGOT_KEEP_FACT if not ctx or ctx in ("—", "-") else ctx + " " + NEGOT_KEEP_FACT
        log.append("%s: eco.rationale снят (редундант структурных полей), факт о длительности переговоров → eco.context" % NEGOT_ID)
        if write:
            set_field(negot, "eco.context", new_ctx)
            set_field(negot, "eco.rationale", "—")

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
