# -*- coding: utf-8 -*-
"""Карточка g707211ba (консорциум Тодда Боэли / зарубежные активы ЛУКОЙЛа),
правки после второго чтения 25 ноября 2026 — то, что не ложится в FIXES:

1. Предмет отвязан от профиля g199de75d («иностранные активы ЛУКОЙЛа»).
   Читатель: в посте заголовок говорит «зарубежные активы», а строка
   «Предмет» — «иностранные активы ЛУКОЙЛа» со строчной буквы (имя общего
   профиля, пост берет его раньше текста `asset`). Предмет здесь — лот,
   совокупность активов в 11 странах, а не компания: по
   CARD_ACCEPTANCE_BRIEF.md лоту профиль не обязателен, `asset` — текст,
   причина — в `accepted_notes.no_profile.target`. Общий профиль не
   переименовывался: он стоит предметом у g75920ee3.
2. Заметка этапа: «Лукойлом» -> «ЛУКОЙЛом» — одно написание компании по всей
   карточке, как у профиля продавца (review.py элемент списка не адресует,
   proofread.py не меняет написание имени).

Запуск: python3 pipeline/archive/2026-11/fix_g707211ba_second_reading_2026_11_25.py --write
"""
import json
import sys

PATH = "static/data/pending.json"
CARD_ID = "g707211ba"
OLD_TARGET = "g199de75d"
OLD_NOTE = ("Тодд Боэли объявил, что его консорциум подписал соглашение с «Лукойлом»: "
            "бумаги компании обменивают на ее зарубежные активы. Для закрытия нужна лицензия OFAC.")
NEW_NOTE = ("Тодд Боэли объявил, что его консорциум подписал соглашение с ЛУКОЙЛом: "
            "бумаги компании обменивают на ее зарубежные активы. Для закрытия нужна лицензия OFAC.")


def main(write):
    with open(PATH, encoding="utf-8") as f:
        base = json.load(f)
    card = next(c for c in base["cards"] if c["id"] == CARD_ID)
    n = 0
    if "target" in card:
        assert card["target"] == OLD_TARGET, "target уже другой: %r" % card["target"]
        assert card.get("asset"), "нет текста предмета — отвязывать профиль нельзя"
        del card["target"]
        print("%s: target %s снят, предмет текстом: %s" % (CARD_ID, OLD_TARGET, card["asset"]))
        n += 1
    ev = card["events"][0]
    if ev["note"] != NEW_NOTE:
        assert ev["note"] == OLD_NOTE, "events[0].note уже другой: %r" % ev["note"]
        ev["note"] = NEW_NOTE
        print("%s: events[0].note -> %s" % (CARD_ID, NEW_NOTE))
        n += 1
    if not n:
        print("%s: уже применено — нечего делать." % CARD_ID)
        return
    if write:
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump(base, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО.")
    else:
        print("Сухой прогон — ничего не записано. Добавьте --write.")


if __name__ == "__main__":
    main(write="--write" in sys.argv)
