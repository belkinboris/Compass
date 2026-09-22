# -*- coding: utf-8 -*-
"""Удалить профиль «Москва-Сити» — единственный, который можно удалить.

ЗАЧЕМ. 22 сентября 2026, разбирая каталог компаний, владелец сказал:
«Москва-Сити давай удалим». Это не компания, а район — и в отличие от
остальных 130 объектов, спрятанных из каталога, у него нет ни одной
причины оставаться в базе:
  • ни одна карточка не ссылается на него ни покупателем, ни продавцом, ни
    предметом — ни одной ролью вообще;
  • ни один профиль не называет его в группе, владельцах или портфеле;
  • описания у него нет («Описание компании пока не добавлено»).

Остальные 130 объектов удалять НЕЛЬЗЯ по прямо противоположной причине:
они стоят предметом реальных сделок, и удаление увело бы плашку сторон в
никуда. Поэтому они скрыты из каталога признаком `asset`, а не стёрты —
см. pipeline/mark_catalog_assets_2026_09_22.py.

ПСЕВДОНИМ УХОДИТ ВМЕСТЕ С ПРОФИЛЕМ. `match_keys` — это «под каким ещё
именем искать ЭТУ запись»; запись без профиля ведёт в пустоту, и такой
осиротевший ключ уже ловили раньше (см. KNOWN_ISSUES про Деметра-Холдинг).

    python3 pipeline/delete_moscow_city_profile_2026_09_22.py
    python3 pipeline/delete_moscow_city_profile_2026_09_22.py --write
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "static" / "data" / "deals_promoted.json"
CID = "g2f4ad622"


def main(write: bool) -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    profile = data["companies"].get(CID)
    if profile is None:
        print("Профиля %s уже нет." % CID)
        return 0

    # ПРОВЕРЯЕМ ПЕРЕД УДАЛЕНИЕМ, А НЕ ВЕРИМ ЗАМЕРУ ВЧЕРАШНЕГО ДНЯ: база могла
    # измениться между решением и его применением.
    blob = json.dumps(data["deals"], ensure_ascii=False)
    if CID in blob:
        print("ОТКАЗ: %s упоминается в карточках сделок — удалять нельзя." % CID)
        return 1
    others = [k for k, v in data["companies"].items()
              if k != CID and CID in json.dumps(v, ensure_ascii=False)]
    if others:
        print("ОТКАЗ: на %s ссылаются профили %s" % (CID, ", ".join(others)))
        return 1

    print("Удаляем профиль %s «%s» (%s)" % (CID, profile.get("name"), profile.get("ind")))
    keys = (data.get("match_keys") or {}).get(CID)
    if keys:
        print("   вместе с псевдонимами: %s" % ", ".join(keys))
    if not write:
        print("\n(сухой прогон; чтобы записать — --write)")
        return 0
    data["companies"].pop(CID, None)
    (data.get("match_keys") or {}).pop(CID, None)
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("\nзаписано")
    return 0


if __name__ == "__main__":
    sys.exit(main("--write" in sys.argv))
