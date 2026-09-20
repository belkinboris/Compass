# -*- coding: utf-8 -*-
"""«Как устроена сделка» держит историю, а не механику — партия по law.struct.

Аудит 13 сентября: `law.struct` подписан «юрлица, этапы, SPV» — механика
ИМЕННО этой сделки. Самый частый промах поля — история ДО сделки (банкротства,
прежние владельцы), опровержение стороны (по правилу единственное законное
место для «кто опроверг» — `eco.context`), кадровые назначения, события ПОСЛЕ
сделки, история несостоявшихся торгов, фон о покупателе.

Каждая запись здесь — либо целое поле (когда весь его текст об одном и том же
постороннем сюжете), либо одно предложение внутри него (когда рядом стоят
и законная механика, и посторонний факт) — решено чтением самого текста
карточки, не автоматикой: `pipeline.fix_audit_move_utils.extend_to_sentences`
только раздвигает готовую цитату до границ предложения, чтобы не оставить
обрывок.

    python3 pipeline/fix_audit_struct_context_2026_09_20.py
    python3 pipeline/fix_audit_struct_context_2026_09_20.py --write
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "static" / "data" / "deals_promoted.json"
sys.path.insert(0, str(ROOT))

from pipeline import audit_queue as aq  # noqa: E402
from pipeline.fix_audit_move_utils import apply_move  # noqa: E402

# Поле целиком не о механике ЭТОЙ сделки — уезжает всё.
WHOLE = ["g08d1c155", "gddb34475", "gd1f94881"]

# Одно предложение — рядом законная механика, трогать её нельзя.
SENTENCE_IDS = [
    "gd9ccfdd2", "gadd238c3", "g34b9af03", "g10053480", "cacdb5edc",
    "g1664083c", "ge292671d", "g4b447867", "c4341479b", "gdc4ff4ab",
    "g3e3f233c", "g22000f22", "gd0d10f9f", "g739d9094", "g8348fea5",
    "ge9b4ba4d", "g1437f510", "g31541607", "c3e0b0e8f", "g9fdcb59d",
    "gf0b712ef", "g39752167", "g560e3f93",
    "gmru-rodnye-polya", "gmru-vostok-sever-pevek", "gc991514e", "g2f572b66",
]

# gcdec4f24: посторонняя история банкротств 2017–2020 — только первые четыре
# предложения (после них начинается механика самой сделки: продавец,
# периметр, покупатель).
PARTIAL_ID = "gcdec4f24"
PARTIAL_QUOTE = (
    "АО «1-я ювелирная сеть», управляющее магазинами «Адамас», до 2022 года "
    "принадлежало «Адамас-ювелирторгу», которое ликвидировано после "
    "банкротства."
)


def main(write: bool) -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    cards = {d["id"]: d for d in data["deals"]}
    decided = aq.decided_by_a_reader()
    log: list = []
    findings = aq.load_findings()
    by_card_quote = {}
    for f in findings:
        if f["class"] == "FIELD_MISPLACED" and f["field"] == "law.struct":
            by_card_quote.setdefault(f["card_id"], f["quote"])

    for cid in WHOLE:
        card = cards[cid]
        full = (card.get("law") or {}).get("struct") or ""
        apply_move(card, "law.struct", full, "eco.context", write, decided, cid, log)

    for cid in SENTENCE_IDS:
        card = cards[cid]
        quote = by_card_quote.get(cid)
        if not quote:
            log.append("%s: цитата не найдена в находках — пропущено" % cid)
            continue
        apply_move(card, "law.struct", quote, "eco.context", write, decided, cid, log)

    card = cards[PARTIAL_ID]
    full = card["law"]["struct"]
    assert full.startswith(PARTIAL_QUOTE)
    end_marker = "начала уступать позиции конкурентам."
    idx = full.find(end_marker)
    assert idx > 0
    chunk = full[: idx + len(end_marker)]
    apply_move(card, "law.struct", chunk, "eco.context", write, decided, PARTIAL_ID, log)

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
