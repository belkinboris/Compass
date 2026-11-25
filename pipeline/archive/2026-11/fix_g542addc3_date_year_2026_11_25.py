# -*- coding: utf-8 -*-
"""Карточка g542addc3 (ОМК / Волгореченский трубный завод), приемка 25 ноября
2026: `date`/`events[0].date` несли 2026-11-25 — день публикации ТАСС и
«Энергетической политики», а не день закрытия сделки. Ни один из трех
источников карточки не называет день самой продажи: «Энергетическая
политика» и ТАСС пишут о покупке без даты события, Smart-lab (со ссылкой на
«Интерфакс», 5 августа 2026) говорит только, что ФАС одобрила сделку «в
начале лета 2026 года», и сам пост датирован 5 августа, но не называет день
закрытия. По правилу «Нет дня — только год» (docs/card_status_dates.md) —
снятие дня; review.py не пишет дату в этом формате (date_is_supported
требует ГГГГ-ММ-ДД), поэтому — прямая запись, как у
pipeline/archive/2026-11/fix_gb82efd9f_date_year_2026_11_19.py.

Запуск: python3 pipeline/archive/2026-11/fix_g542addc3_date_year_2026_11_25.py --write
"""
import json
import sys

PATH = "static/data/pending.json"
CARD_ID = "g542addc3"
OLD_DATE = "2026-11-25"
NEW_DATE = "2026"


def main(write):
    with open(PATH, encoding="utf-8") as f:
        base = json.load(f)
    card = next(c for c in base["cards"] if c["id"] == CARD_ID)
    assert card["date"] == OLD_DATE, "date уже другой: %r" % card["date"]
    assert card["events"][0]["date"] == OLD_DATE, "events[0].date уже другой: %r" % card["events"][0]["date"]
    card["date"] = NEW_DATE
    card["events"][0]["date"] = NEW_DATE
    print("%s: date -> %s, events[0].date -> %s" % (CARD_ID, NEW_DATE, NEW_DATE))
    if write:
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump(base, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО.")
    else:
        print("Сухой прогон — ничего не записано. Добавьте --write.")


if __name__ == "__main__":
    main(write="--write" in sys.argv)
