# -*- coding: utf-8 -*-
"""Приемка карточек G23 (архив канала @alumnipartnerslawfirm): events[0].note
(обрыв многоточием — индексированный путь не читается review.set_field) и
law.adv (списочное поле — generic-проверка review.check() требует
буквального совпадения ВСЕЙ строки `new` внутри `quote`, недостижимого для
списка). Оба поля правятся прямой записью, как g1c8087ad и его скрипт.

Источники — проектные страницы ALUMNI Partners (уже в src карточек)."""
import json
import sys

PATH = "static/data/pending.json"

EDITS = [
 {"id": "ge31110bc",
  "old_note": ('ВымпелКом купил 44% ООО «Вока-Тек». ALUMNI Partners сопровождала ВымпелКом в сделке по '
               'приобретению доли в Voca-Tech 🤝 ALUMNI Partners выступила юридическим консультантом '
               'ПАО «ВымпелКом» в сделке по приобретению 44% долей в уставном капитале ООО «Вока-Тек»…'),
  "new_note": ('Юридическим консультантом ВымпелКома по сделке выступила ALUMNI Partners — сопровождала '
               'due diligence и структурирование, включая вопросы трансграничной реструктуризации группы '
               '«Вока-Тек».'),
  "adv": [["Юридический консультант покупателя", "ALUMNI Partners",
           "«Команда ALUMNI Partners выступила юридическим консультантом ПАО «ВымпелКом» в сделке по "
           "приобретению 44% долей в уставном капитале ООО «Вока-Тек»». Источник: alumnipartners.ru"]]},
 {"id": "gb7b2da31",
  "old_note": ('Фонд Pre-IPO 1 (ВИМ Инвестиции) продал пакет GetCourse. ALUMNI Partners сопровождала '
               'выход Фонда Pre-IPO 1 из капитала GetCourse 🎓 Команда ALUMNI Partners выступила '
               'юридическим консультантом на стороне покупателя в рамках сделки по приобретению '
               'пакета в…'),
  "new_note": ('Юридическим консультантом покупателя выступила ALUMNI Partners — готовила документы, '
               'вела переговоры и организовала подписание и закрытие сделки.'),
  "adv": [["Юридический консультант покупателя", "ALUMNI Partners",
           "«Команда ALUMNI Partners выступила юридическим консультантом на стороне покупателя в "
           "рамках сделки по приобретению пакета в капитале GetCourse». Источник: alumnipartners.ru"]]},
]


def main(write):
    with open(PATH, encoding="utf-8") as f:
        base = json.load(f)
    by_id = {c["id"]: c for c in base["cards"]}
    for e in EDITS:
        card = by_id[e["id"]]
        assert card["events"][0]["note"] == e["old_note"], "%s: events[0].note уже другой" % e["id"]
        assert card["law"]["adv"] == [], "%s: law.adv уже другой" % e["id"]
        card["events"][0]["note"] = e["new_note"]
        card["law"]["adv"] = e["adv"]
        print("%s: events[0].note дописан, law.adv записан" % e["id"])
    if write:
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump(base, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО.")
    else:
        print("Сухой прогон — ничего не записано. Добавьте --write.")


if __name__ == "__main__":
    main(write="--write" in sys.argv)
