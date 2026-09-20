# -*- coding: utf-8 -*-
"""«~2 млрд ₽» и «≈2 млрд ₽» — одна и та же цена, написанная двумя способами.

Аудит 13 сентября 2026 и приёмка карточек считали такие пары расхождением
суммы на «Обзоре» и в «Экономисте» — формально справедливо: строки разные,
и проверка не может знать, что тильда и знак «≈» значат одно. Но читателю
это не расхождение, а неряшливость: в одной карточке цена написана так, в
соседней иначе.

Замер по базе: знак «≈» стоит в 78 полях суммы, тильда — в 44. Приводим к
тому, что и так преобладает и правильнее для русского текста. Цифра,
валюта и оговорки не трогаются: меняется один знак.

    python3 pipeline/fix_audit_tilde_2026_09_20.py
    python3 pipeline/fix_audit_tilde_2026_09_20.py --write
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "static" / "data" / "deals_promoted.json"


def main(write: bool) -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    touched, matched = [], 0
    for d in data["deals"]:
        eco = d.get("eco") if isinstance(d.get("eco"), dict) else None
        before = ((d.get("sum") or ""), (eco or {}).get("sum") or "")
        if "~" not in before[0] and "~" not in before[1]:
            continue
        new_sum = (d.get("sum") or "").replace("~", "≈")
        new_eco = ((eco or {}).get("sum") or "").replace("~", "≈")
        assert new_sum.count("≈") >= before[0].count("≈")
        touched.append((d["id"], before[0], new_sum, before[1], new_eco))
        if new_sum and new_eco and new_sum == new_eco and before[0] != before[1]:
            matched += 1
        if write:
            if d.get("sum"):
                d["sum"] = new_sum
            if eco is not None and eco.get("sum"):
                eco["sum"] = new_eco
    assert touched, "тильды в суммах больше нет — правка применена"

    print("Карточек, где тильда заменена знаком «≈»: %d" % len(touched))
    print("Из них сумма на «Обзоре» и в «Экономисте» после этого совпала: %d" % matched)
    for cid, s0, s1, e0, e1 in touched[:6]:
        print("   %-12s «%s» → «%s»" % (cid, (s0 or e0)[:40], (s1 or e1)[:40]))
    if not write:
        print("\n(сухой прогон; чтобы записать — --write)")
        return 0
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nзаписано")
    return 0


if __name__ == "__main__":
    sys.exit(main("--write" in sys.argv))
