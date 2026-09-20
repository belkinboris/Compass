# -*- coding: utf-8 -*-
"""Связка Vizant — Аркадий Ротенберг подтверждена источником владельца.

БЫЛО. Карточка `g016f1b13` называла конечным бенефициаром Аркадия
Ротенберга, но ни один из четырёх её источников этого не говорил: ссылка на
Коммерсантъ была о другом человеке, а vizantgroup.ru и ibcrealestate.ru
писали только «покупателем стала компания Vizant», без имени бенефициара.
Вопрос ушёл владельцу.

СТАЛО. Владелец 20 сентября 2026 прислал источник — TAdviser, страница
Les Art Resort. Прочитано дословно:

    «Управляющая компания Vizant, принадлежащая бизнесмену Аркадию
    Ротенбергу, взяла в управление отель LesArt Resort в Подмосковье,
    оценочная стоимость которого составляет от ₽6 до ₽7 млрд.»

плюс в шапке страницы «Собственники: Vizant» и заголовок раздела
«2025: Компания Аркадия Ротенберга купила LesArt Resort».

ЧТО ЭТО ЗАКРЫВАЕТ И ЧТО НЕТ. Подтверждено ровно то, чего не хватало:
Vizant принадлежит Ротенбергу. ЗПИФ «Терс» и ООО «УК ФИН-ПАРТНЕР» этот
источник НЕ упоминает — фраза о них остаётся в карточке как была, со
своими источниками, и новым подтверждением не обрастает: подтверждать
цитатой то, чего в цитате нет, — ровно та ошибка, из-за которой вопрос и
возник.

Запуск: python3 pipeline/fix_lesart_rotenberg_source.py --write
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "static" / "data" / "deals_promoted.json"
DEAL_ID = "g016f1b13"
SRC = ["TAdviser", "https://www.tadviser.ru/index.php/Компания:Les_Art_Resort_%28Лес_Арт_Резорт%29"]


def main(write: bool) -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    deal = next(d for d in data["deals"] if d["id"] == DEAL_ID)
    urls = {s[1] for s in (deal.get("src") or []) if isinstance(s, list) and len(s) > 1}
    assert SRC[1] not in urls, "источник уже добавлен"
    assert "Ротенберг" in (deal.get("extra") or ""), "фразы о бенефициаре в карточке уже нет"

    if write:
        deal.setdefault("src", []).append(SRC)
        json.dump(data, DATA.open("w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("карточка %s: источников %d → %d" % (DEAL_ID, len(urls), len(urls) + 1))
    print("добавлен:", SRC[0], SRC[1])
    if not write:
        print("\n(сухой прогон; чтобы записать — --write)")
        return 0
    print("\nзаписано")
    return 0


if __name__ == "__main__":
    sys.exit(main("--write" in sys.argv))
