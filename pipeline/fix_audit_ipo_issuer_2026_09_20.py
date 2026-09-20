# -*- coding: utf-8 -*-
"""На IPO компания не покупает себя: эмитент — предмет сделки, а не покупатель.

Что чинит (класс ROLE_WRONG из аудита 13 сентября 2026, повторяющийся
подкласс). Из 40 карточек об IPO и pre-IPO девятнадцать устроены правильно:
компания, чьи акции размещаются, стоит предметом сделки, покупателя нет —
на бирже покупателей тысячи, и назвать одного нельзя. У двадцати та же
компания стояла ПОКУПАТЕЛЕМ, то есть карточка утверждала, что «Делимобиль»
купил «Делимобиля». Половина карточек одного типа противоречила другой
половине.

Разбирается по одной, а не правилом: две карточки из двадцати трогать
нельзя, и увидеть это можно только прочитав заголовок.
  • «Суточно.ру» привлекло инвестиции pre-IPO фондов ВИМ Инвестиции —
    там покупателем стоит фонд, и это верно;
  • «Финам» создаёт Pre-IPO фонд — «Финам» создаёт фонд, а не размещается.

Чтобы это не вернулось, проверка «эмитент стоит покупателем» добавлена в
приёмку новой карточки (accept_card.findings, признак `ipo_issuer_as_buyer`).

    python3 pipeline/fix_audit_ipo_issuer_2026_09_20.py
    python3 pipeline/fix_audit_ipo_issuer_2026_09_20.py --write
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "static" / "data" / "deals_promoted.json"

# id карточки → как называется эмитент в заголовке (для проверки, что
# переносим именно его профиль, а не чей-то чужой).
MOVE = {
    "g167e415a": "Делимобил",
    "g41eb17f6": "Озон Фармацевтика",
    "g68ebf773": "нструменты",
    "g5612a3b3": "IVA Technologies",
    "g6ba5f232": "Элемент",
    "g0be691b7": "Бери заряд",
    "g00a0318e": "Займер",
    "g3ed36abe": "Европлан",
    "gb21ab6d1": "Кристалл",
    "g202f49be": "Диасофт",
    "gaa7602e7": "Цифровые привычки",
    "g6a453b19": "Ultimate Education",
    "gbfbab63c": "Henderson",
    "g572a4aca": "Мосгорломбард",
    "g4e3b91d7": "Совкомбанк",
    "g5f24bb26": "ЕвроТранс",
    "g58d70492": "Whoosh",
    "inkab-ipo": "Инкаб",
}
# Прочитаны и оставлены как есть — покупатель там настоящий.
KEEP = {"g7e470153": "покупателем стоит фонд «ВИМ Инвестиции», он и есть инвестор",
        "c3c15a888": "«Финам» создаёт фонд, а не размещает свои акции"}


def main(write: bool) -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    cards = {d["id"]: d for d in data["deals"]}
    names = {cid: c.get("name", "") for cid, c in data["companies"].items()}

    done = []
    for cid, marker in MOVE.items():
        d = cards[cid]
        assert (d.get("type") or "") == "IPO", (cid, d.get("type"))
        buyer = d.get("buyer")
        assert buyer, "%s: покупателя уже нет — правка применена" % cid
        assert not d.get("target"), "%s: предмет уже стоит" % cid
        assert marker.lower() in names[buyer].lower() or marker.lower() in d["title"].lower(), \
            (cid, marker, names[buyer])
        done.append((cid, names[buyer], d["title"][:60]))
        if write:
            d["target"] = buyer
            d.pop("buyer", None)
            d.pop("buyer_name", None)

    print("Эмитент переставлен из покупателей в предмет сделки: %d" % len(done))
    for cid, nm, title in done:
        print("   %-12s %-28s %s" % (cid, nm[:28], title))
    print("Оставлено как есть после чтения: %d" % len(KEEP))
    for cid, why in KEEP.items():
        print("   %-12s %s" % (cid, why))
    if not write:
        print("\n(сухой прогон; чтобы записать — --write)")
        return 0
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nзаписано")
    return 0


if __name__ == "__main__":
    sys.exit(main("--write" in sys.argv))
