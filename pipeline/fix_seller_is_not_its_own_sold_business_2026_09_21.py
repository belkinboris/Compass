# -*- coding: utf-8 -*-
"""Продавец не может быть профилем бизнеса, который он же продал.

ЧТО НАШЛОСЬ. У четырёх карточек `seller_id` вёл на профиль ПРОДАННОГО
актива: «Heineken продал активы в России» — продавец «Heineken (российский
бизнес)»; то же у двух сделок Viterra и у Canpack. На сайте это значит, что
сделка показывается на странице проданной компании как её собственная
продажа, а настоящего продавца — материнской компании — на карточке нет
вовсе.

ОТКУДА ЭТО ВЗЯЛОСЬ. У 17 профилей-дочек вида «Knauf (российский бизнес)»
среди псевдонимов стоит голое имя МАТЕРИ («knauf»), и ключ поиска у них
один. Привязка по имени поэтому и попадала в дочку. Нашли читатели очереди
аудита 21 сентября на парах Natura&Co / Avon и SoftwareONE, проверка по
всей базе дала эти четыре живых случая.

ЧТО СДЕЛАНО. Неверная ссылка снята, имя продавца остаётся текстом: пустое
поле честнее неверного, а профили самих Heineken, Viterra и Canpack в базе
ещё не заведены (они в списке `pipeline/profiles_to_create_2026_09_21.json`
— как заведут, ссылку поставят на них).

ЧТОБЫ НЕ ВЕРНУЛОСЬ — два забора, а не один: запрет в `link_parties.py`
(там, где роль решается) и инвариант по всей базе в `test_data.py`.

    python3 pipeline/fix_seller_is_not_its_own_sold_business_2026_09_21.py
    python3 pipeline/fix_seller_is_not_its_own_sold_business_2026_09_21.py --write
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "static" / "data" / "deals_promoted.json"
sys.path.insert(0, str(ROOT / "pipeline" / "ingest"))

from link_parties import _is_parent_of_subsidiary  # noqa: E402

ROLES = (("seller_id", "seller"), ("buyer", "buyer_name"))


def offenders(data):
    out = []
    for card in data["deals"]:
        for id_field, text_field in ROLES:
            cid = card.get(id_field)
            if not cid:
                continue
            name = (data["companies"].get(cid) or {}).get("name") or ""
            text = str(card.get(text_field) or "")
            if text and _is_parent_of_subsidiary(text, name):
                out.append((card, id_field, text, name))
    return out


def main(write: bool) -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    found = offenders(data)
    if not found:
        print("Таких карточек нет — всё уже починено.")
        return 0
    print("Сторона привязана к профилю своего же проданного бизнеса: %d" % len(found))
    for card, id_field, text, name in found:
        print("   %-12s %s: «%s» → «%s» — ссылка снята, имя остаётся текстом"
              % (card["id"], id_field, text, name))
        if write:
            card.pop(id_field, None)
    if not write:
        print("\n(сухой прогон; чтобы записать — --write)")
        return 0
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nзаписано")
    return 0


if __name__ == "__main__":
    sys.exit(main("--write" in sys.argv))
