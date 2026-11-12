# -*- coding: utf-8 -*-
"""Карточка g1c8087ad (X5 Group / «Виктория Балтия»): два поля, которые
review.py FIXES не берет напрямую — events[0].note (обрыв многоточием,
индексированный путь не читается get_field/set_field) и law.adv (списочное
поле — generic-проверка review.check() требует буквального совпадения ВСЕЙ
строки `new` целиком внутри `quote`, что для списка недостижимо; тот же
класс, что держит fix_g21795ec9_truncated_note.py).

Источник обоих фактов — пресс-релиз ALUMNI Partners (сайт фирмы, рус.
версия, уже в src карточки): alumnipartners.ru/news/alumni-partners-...
"""
import json
import sys

PATH = "static/data/pending.json"
ID = "g1c8087ad"

OLD_NOTE = ('X5 Group купила «Виктория Балтия» (магазины «Виктория»). ALUMNI Partners оказала '
            'юридическую поддержку X5 Group в проекте по приобретению сети магазинов «Виктория '
            'Балтия» Команда ALUMNI Partners выступила юридическим консультантом X5 Group в '
            'рамках сделки по…')
NEW_NOTE = ('Юридическим консультантом X5 Group по сделке выступила компания ALUMNI Partners — '
            'помогала структурировать покупку с точки зрения недвижимости.')
NEW_ADV = [['Юридический консультант покупателя', 'ALUMNI Partners',
            '«Команда ALUMNI Partners выступила юридическим консультантом X5 Group в рамках сделки '
            'по покупке компании «Виктория Балтия»». Источник: alumnipartners.ru']]


def main(write):
    with open(PATH, encoding="utf-8") as f:
        base = json.load(f)
    card = next(c for c in base["cards"] if c["id"] == ID)
    assert card["events"][0]["note"] == OLD_NOTE, "events[0].note уже другой — уже правили?"
    assert card["law"]["adv"] == [], "law.adv уже другой — уже правили?"
    card["events"][0]["note"] = NEW_NOTE
    card["law"]["adv"] = NEW_ADV
    print(f"{ID}: events[0].note дописан, law.adv — ALUMNI Partners")
    if write:
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump(base, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО.")
    else:
        print("Сухой прогон — ничего не записано. Добавьте --write.")


if __name__ == "__main__":
    main(write="--write" in sys.argv)
