# -*- coding: utf-8 -*-
"""Карточка g707211ba (консорциум Тодда Боэли / зарубежные активы ЛУКОЙЛа),
второе чтение 25 ноября 2026: `date`/`events[0].date` несли 2026-11-25 — день,
когда Тодд Боэли объявил о подписании (Reuters: «said on Wednesday he had
signed»), и день публикаций «Коммерсанта» и «Ведомостей». День самого
подписания не называет ни один из четырех источников. По правилу «Дата — день
события, о котором статус» и «Нет дня — только год» (docs/card_status_dates.md)
— год; `date_basis: announcement` снимается вместе с днем (запись FIXES о нем
убрана из партии g707211ba_boehly_lukoil_2026_11_25.py). День объявления
сказан словами в «Дополнительно». review.py дату годом не пишет — прямая
запись, как pipeline/archive/2026-11/fix_g542addc3_date_year_2026_11_25.py.

Запуск: python3 pipeline/archive/2026-11/fix_g707211ba_date_year_2026_11_25.py --write
"""
import json
import sys

PATH = "static/data/pending.json"
CARD_ID = "g707211ba"
OLD_DATE = "2026-11-25"
NEW_DATE = "2026"


def main(write):
    with open(PATH, encoding="utf-8") as f:
        base = json.load(f)
    card = next(c for c in base["cards"] if c["id"] == CARD_ID)
    if card["date"] == NEW_DATE and "date_basis" not in card:
        print("%s: уже применено — нечего делать." % CARD_ID)
        return
    assert card["date"] == OLD_DATE, "date уже другой: %r" % card["date"]
    assert card["events"][0]["date"] == OLD_DATE, "events[0].date уже другой: %r" % card["events"][0]["date"]
    assert card.get("date_basis") == "announcement", "date_basis уже другой: %r" % card.get("date_basis")
    card["date"] = NEW_DATE
    card["events"][0]["date"] = NEW_DATE
    del card["date_basis"]
    print("%s: date -> %s, events[0].date -> %s, date_basis снят" % (CARD_ID, NEW_DATE, NEW_DATE))
    if write:
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump(base, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО.")
    else:
        print("Сухой прогон — ничего не записано. Добавьте --write.")


if __name__ == "__main__":
    main(write="--write" in sys.argv)
