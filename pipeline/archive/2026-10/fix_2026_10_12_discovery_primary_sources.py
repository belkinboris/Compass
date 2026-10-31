# -*- coding: utf-8 -*-
"""Первоисточник вместо агрегатора (качество, 12 октября 2026).

У двух карточек единственным источником был пост @LawFirms — найден
настоящий первоисточник, подтверждающий те же факты (см. KNOWN_ISSUES.md
про кодировку lawfirm.ru). `split_discovery_sources.py --write` после
этого скрипта сам уводит @LawFirms в `discovery_src`.
"""
import io
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "..", "static", "data", "deals_promoted.json")

ADD_SOURCE = [
    ("g2e6254b6", ["Nextons", "https://lawfirm.ru/news/index.php?id=30641"]),
    ("g6e1bb001", ["Коммерсантъ", "https://www.kommersant.ru/doc/7327316"]),
]


def main(write=False):
    with io.open(DATA, encoding="utf-8") as f:
        data = json.load(f)
    deals = {c["id"]: c for c in data["deals"]}

    for card_id, source in ADD_SOURCE:
        card = deals[card_id]
        urls = [s[1] for s in card.get("src") or []]
        assert source[1] not in urls, "%s: источник уже есть" % card_id

    if not write:
        print("Добавится %d источников (сухой прогон)" % len(ADD_SOURCE))
        return

    for card_id, source in ADD_SOURCE:
        deals[card_id]["src"].append(source)

    with io.open(DATA, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("ЗАПИСАНО: %d источников добавлено" % len(ADD_SOURCE))


if __name__ == "__main__":
    import sys
    main(write="--write" in sys.argv)
