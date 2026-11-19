# -*- coding: utf-8 -*-
"""Второе чтение карточки gb82efd9f («Медскан» продал 49% лабораторной сети
KDL), 19 ноября 2026: `date`/`events[0].date` несли день публикации статьи
(2026-11-19 — дата URL РБК и подпись зеркала news.mail.ru, «19 ноября 2026
РБК»), а не день события. Статья не называет день самой продажи 49% KDL —
только пресс-релиз «поступивший в РБК», без даты. Единственный день в
статье, «18 ноября», относится к ДРУГОМУ факту (раскрытие колл-опциона и
гарантии по «Медскан Лаб» через Центр раскрытия корпоративной информации) —
переносить его на продажу KDL было бы такой же догадкой, поэтому он и не
взят. По правилу «Нет дня — только год» (docs/card_status_dates.md) — откат
на год; review.py не пишет дату в этом формате (date_is_supported требует
ГГГГ-ММ-ДД), поэтому — прямая запись, как у
pipeline/archive/2026-11/direct_date_fixes_second_reading_2026_11_12.py.

Источник: РБК, https://www.rbc.ru/business/19/11/2026/6aff3156f3a807b635eff90b
(первоисточник за paywall; текст сверен по зеркалу news.mail.ru/society/73165759/,
data/inbox/raw/2026-11-19-articles.jsonl).

Запуск: python3 pipeline/archive/2026-11/fix_gb82efd9f_date_year_2026_11_19.py --write
"""
import json
import sys

PATH = "static/data/pending.json"
CARD_ID = "gb82efd9f"
OLD_DATE = "2026-11-19"
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
