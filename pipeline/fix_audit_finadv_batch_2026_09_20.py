# -*- coding: utf-8 -*-
"""«Финансовые консультанты» несут оценщиков, сторону сделки и механику торгов.

Аудит 13 сентября: поле `eco.finadv` — про финансовых консультантов СТОРОН
сделки, а держало у части карточек независимых оценщиков (роль «оценка —
не консультант», уже записанное правило), организатора торгов, и один раз —
саму сторону сделки под видом консультанта (NBIM — сама продавец, не
советник продавца).

Три записи — чистое дублирование: факт уже правильно стоит в `eco.val` или
`seller`, из finadv он просто убирается (ничего не теряется). Три —
переезжают: организатор торгов в `law.struct` (механика, не консультация),
оценка Kroll — в `eco.val` (независимая оценка, там ей место), юридическая
фирма Latham & Watkins — в `law.adv` вторым консультантом (Dechert LLP уже
стоит там как консультант ДРУГОЙ стороны той же сделки).

    python3 pipeline/fix_audit_finadv_batch_2026_09_20.py
    python3 pipeline/fix_audit_finadv_batch_2026_09_20.py --write
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "static" / "data" / "deals_promoted.json"

# Дубли: факт уже верно стоит в другом поле — finadv просто очищается.
DUPES = {
    "ge8f45161": "Infoline-Аналитика (независимая оценка стоимости пакета, "
                 "комментарий гендиректора Михаила Бурмистрова)",
    "gc3d735fc": "АО «Деловые решения и технологии» (бывшая Deloitte) — "
                 "независимый оценщик на стороне ЦБ (продавца); PwC — "
                 "оценка «Открытия» при подготовке к IPO, до сделки",
    "g3074f98b": "Norges Bank Investment Management (NBIM) — управляющий "
                 "фондом, ответственный за исполнение продажи",
}

# Переезжает целиком в другое поле сделки.
MOVES = [
    ("ge386fb20", "BGP Capital (Юрий Левицкий, инвестиционный директор — "
                  "независимая оценка стоимости актива, не подтверждён как "
                  "официальный советник)", "eco", "val"),
    ("g66bb0d00", "РОСЭЛТОРГ (АО «Единая электронная торговая площадка») — "
                  "организатор торгов", "law", "struct"),
]

# g3cc2009d: из finadv уходит только оценка Kroll — Opus Group и AlixPartners
# остаются (AlixPartners действительно финансовый советник совета директоров).
KROLL_ID = "g3cc2009d"
KROLL_QUOTE = "Kroll — независимый оценщик активов Petropavlovsk (оценка: $458–621 млн)"

# g39752167: юрфирма переезжает в law.adv вторым консультантом (Dechert LLP
# уже стоит там консультантом Kinross Gold — другой стороны той же сделки).
LAW_ID = "g39752167"
LAW_QUOTE = "Latham & Watkins LLP — консультант Highland Gold Mining"


def main(write: bool) -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    cards = {d["id"]: d for d in data["deals"]}
    applied = []

    for cid, quote in DUPES.items():
        card = cards[cid]
        cur = card["eco"].get("finadv") or ""
        assert quote in cur, "%s: дубль не найден дословно" % cid
        applied.append((cid, "eco.finadv", "удалено (дубль)", quote[:55]))
        if write:
            card["eco"]["finadv"] = "—"

    for cid, quote, da, db in MOVES:
        card = cards[cid]
        cur = card["eco"].get("finadv") or ""
        assert quote in cur, "%s: текст не найден дословно" % cid
        dst = card.setdefault(da, {})
        old = dst.get(db)
        new = quote if not old or old in ("—", "-", "") else (old + " " + quote)
        applied.append((cid, "eco.finadv", "%s.%s" % (da, db), quote[:55]))
        if write:
            dst[db] = new
            card["eco"]["finadv"] = "—"

    kroll = cards[KROLL_ID]
    cur = kroll["eco"].get("finadv") or ""
    assert KROLL_QUOTE in cur
    val = kroll["eco"].get("val") or ""
    applied.append((KROLL_ID, "eco.finadv", "eco.val", KROLL_QUOTE[:55]))
    if write:
        kroll["eco"]["val"] = (val + " " + KROLL_QUOTE).strip()
        kroll["eco"]["finadv"] = cur.replace(KROLL_QUOTE, "").strip(" ;")

    law = cards[LAW_ID]
    cur = law["eco"].get("finadv") or ""
    assert LAW_QUOTE in cur
    applied.append((LAW_ID, "eco.finadv", "law.adv", LAW_QUOTE[:55]))
    if write:
        adv = law.setdefault("law", {}).setdefault("adv", [])
        adv.append(["Юридический консультант", "Latham & Watkins LLP",
                    "консультант Highland Gold Mining"])
        law["eco"]["finadv"] = "—"

    print("Обработано записей: %d" % len(applied))
    for cid, src, dst, snippet in applied:
        print("   %-14s %-14s → %-20s «%s…»" % (cid, src, dst, snippet))

    if not write:
        print("\n(сухой прогон; чтобы записать — --write)")
        return 0
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nзаписано")
    return 0


if __name__ == "__main__":
    sys.exit(main("--write" in sys.argv))
