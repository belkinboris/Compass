# -*- coding: utf-8 -*-
"""Второе чтение нашло, что у двух карточек дата — день публикации
пресс-релиза консультанта, а не дата события; источники называют только
месяц (gb7b2da31) или вообще не называют день (g5db4bcc2). По правилу
«Нет дня — только год» (docs/card_status_dates.md) — откат на год, месяц
словами переносится в прозу. review.py не пишет date в этом формате
(date_is_supported требует ГГГГ-ММ-ДД), поэтому — прямая запись, как
events[N] у других карточек этого цикла."""
import json
import sys

PATH = "static/data/pending.json"

EDITS = [
 {"id": "gb7b2da31", "old_date": "2025-11-24", "new_date": "2025",
  "old_event_date": "2025-11-24", "new_event_date": "2025",
  "eco_context_add": (" Сама сделка (переход доли к «Инвесттехцентру») прошла в августе 2025 года — ALUMNI "
                       "Partners опубликовала пресс-релиз о своей роли в ней позже, 24 ноября.")},
 {"id": "g5db4bcc2", "old_date": "2025-12-08", "new_date": "2025",
  "old_event_date": "2025-12-08", "new_event_date": "2025",
  "eco_context_add": None},
]


def main(write):
    with open(PATH, encoding="utf-8") as f:
        base = json.load(f)
    by_id = {c["id"]: c for c in base["cards"]}
    for e in EDITS:
        card = by_id[e["id"]]
        assert card["date"] == e["old_date"], "%s: date уже другой" % e["id"]
        assert card["events"][0]["date"] == e["old_event_date"], "%s: events[0].date уже другой" % e["id"]
        card["date"] = e["new_date"]
        card["events"][0]["date"] = e["new_event_date"]
        if e["eco_context_add"]:
            card["eco"]["context"] += e["eco_context_add"]
        print("%s: date -> %s, events[0].date -> %s" % (e["id"], e["new_date"], e["new_event_date"]))
    if write:
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump(base, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО.")
    else:
        print("Сухой прогон — ничего не записано. Добавьте --write.")


if __name__ == "__main__":
    main(write="--write" in sys.argv)
