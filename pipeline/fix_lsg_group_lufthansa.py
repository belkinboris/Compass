# -*- coding: utf-8 -*-
"""«LSG Group Lufthansa» — компании с таким названием не существует.

СИМПТОМ. В карточке «Аэрофлот»/«Аэромар» (g2c27516d) продавец 49% назван
«немецкая LSG Group Lufthansa», и то же сочетание стоит в описании профиля
Truffle 2 GmbH. Найдено по замечанию партнёров 19 сентября 2026.

ПРОВЕРКА ПО ИСТОЧНИКАМ КАРТОЧКИ (три из семи, прочитаны в тот же день):
  * Интерфакс (interfax.ru/business/1112456) — «"Аэрофлот" выкупил у
    структуры Lufthansa (Германия) 49% в "Аэромаре"», «принадлежащих
    Truffle 2 GmbH (аффилирована с Lufthansa)». Слова LSG в тексте НЕТ.
  * mergers.ru/news/…-87461 — те же две фразы, LSG не упоминается.
  * RB.ru — «выкупить у немецкой Lufthansa 49% "Аэромара"». LSG Sky Chefs
    там есть, но в справке о 1996 годе: «совместное предприятие Lufthansa
    Service Holding и канадской Onex Food Service» — это про другую эпоху
    и другое юрлицо, к продавцу 2026 года отношения не имеет.

ЧТО НЕ ТАК. Ни один источник не называет продавца «LSG Group». Само
сочетание «LSG Group Lufthansa» склеивает два разных названия в одно
несуществующее — ровно тот класс дефекта, от которого защищает правило
«не подменять отсутствующие данные правдоподобными»: LSG Group
действительно была кейтеринговым подразделением Lufthansa, но это не
делает её именем продавца в этой сделке.

ЧИНИМ на то, что источники говорят дословно: продавец — немецкая
Lufthansa через дочернюю структуру Truffle 2 GmbH.

post_override не трогаем: пост уже ушёл подписчикам, и переписывать
запись о том, что было отправлено, значит потерять след. Правка вышедшего
поста — отдельная операция и не здесь.

Запуск: python3 pipeline/fix_lsg_group_lufthansa.py --write

Лежит в pipeline/, а не в pipeline/ingest/fixes/: тот каталог занят
таблицами FIXES для review.py, и любой файл без такой таблицы ломает
сбор тестов. Разовые правки базы живут рядом с fix_vtb_ordinal_ranking.py.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "static" / "data" / "deals_promoted.json"

DEAL_ID = "g2c27516d"
PROFILE_ID = "g21e04900"

SHARE_OLD = ("Ранее 49% компании через дочернюю структуру Truffle 2 GmbH владела "
             "немецкая LSG Group Lufthansa")
SHARE_NEW = ("Ранее 49% компании через дочернюю структуру Truffle 2 GmbH владела "
             "немецкая Lufthansa")

DESC_OLD = "Немецкая структура, аффилированная с Lufthansa (LSG Group);"
DESC_NEW = "Немецкая структура, аффилированная с Lufthansa;"


def main(write: bool) -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))

    deal = next(d for d in data["deals"] if d["id"] == DEAL_ID)
    share = deal["eco"]["share"]
    assert SHARE_OLD in share, "формулировка в карточке уже другая — проверьте руками"
    deal["eco"]["share"] = share.replace(SHARE_OLD, SHARE_NEW)

    profile = data["companies"][PROFILE_ID]
    assert DESC_OLD in profile["desc"], "описание профиля уже другое — проверьте руками"
    profile["desc"] = profile["desc"].replace(DESC_OLD, DESC_NEW)

    # Больше «LSG» в базе остаться не должно нигде, кроме уже отправленного поста.
    rest = [d["id"] for d in data["deals"]
            if "LSG" in json.dumps({k: v for k, v in d.items() if k != "post_override"},
                                   ensure_ascii=False)]
    assert not rest, "LSG остался в карточках: %s" % rest

    print("карточка %s: %s" % (DEAL_ID, deal["eco"]["share"][:160]))
    print("профиль %s: %s" % (PROFILE_ID, profile["desc"][:160]))
    if not write:
        print("\n(сухой прогон; чтобы записать — --write)")
        return 0
    # indent=1 — как файл лежит в git. Любой другой отступ переписал бы
    # все 8 МБ и превратил правку двух строк в нечитаемый diff.
    # indent=1 и БЕЗ завершающего перевода строки — ровно как файл лежит
    # в git (так же пишут остальные скрипты правок). Любое другое
    # форматирование переписало бы все 8 МБ и превратило правку двух
    # строк в нечитаемый diff.
    json.dump(data, DATA.open("w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\nзаписано")
    return 0


if __name__ == "__main__":
    sys.exit(main("--write" in sys.argv))
