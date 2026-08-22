# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка gd21bbce8 (Натиксис-банк/
«Бюрократ»): `eco.context` заканчивался на прежней сделке того же
покупателя (Джей энд Ти Банк). Дельта нашла дальнейшую судьбу самого
Натиксис-банка: 10 июля 2025 он переименован в «НТХ Банк» (по данным
ЕГРЮЛ) — «что было дальше» после этой сделки. Окончательный итог
(присоединение НТХ Банка к Реалист Банку в 2026 году) внесён отдельно,
через review.py, в `law.struct` (поле пустовало).

Не через review.py: `eco.context` уже не пуст, а общая проверка
дословности требует, чтобы ВСЁ значение поля (старый текст + новый)
лежало в ОДНОЙ цитате — старый текст из Интерфакса о самой сделке, новый
— из отдельной статьи (Bosfera.ru, 11.07.2025) про переименование.
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gd21bbce8'
OLD_CONTEXT = (
    'Это не первый небольшой банк с иностранным капиталом, '
    'приобретаемый «Бюрократом». В декабре 2023 года компания закрыла '
    'сделку по покупке российского Джей энд Ти Банка у чешского J&T '
    'banka. «Бюрократу» также принадлежит Реалист банк. Присоединение '
    'Джей энд Ти Банка к Реалист банку завершилось в июле 2024 года.'
)
ADDITION = (
    'Натиксис Банк, ранее принадлежащий французскому Natixis, 10 июля '
    '2025 года изменил свое название на НТХ Банк, следует из данных '
    'ЕГРЮЛ.'
)
NEW_CONTEXT = OLD_CONTEXT + ' ' + ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"

    print(f"{CARD_ID} eco.context: += переименование Натиксис Банка в "
          "«НТХ Банк» (10 июля 2025)")
    deal['eco']['context'] = NEW_CONTEXT

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО")
    else:
        print("Сухой прогон. Запись — с --write.")


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
