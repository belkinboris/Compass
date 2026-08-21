# -*- coding: utf-8 -*-
"""ГК «Полипласт»/«Русский Хром 1915» (`g03ae93e7`): месячный дообыск
подтвердил, что переименование в «Хромпик» состоялось (заголовок
Коммерсанта), и нашёл инвестиционную программу и производственные
итоги после сделки — из источника, отличного от уже занятого поля
`eco.context`. Слияние разовым скриптом.

Запуск: python3 pipeline/fix_hrompik_followup.py           # проверка
        python3 pipeline/fix_hrompik_followup.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g03ae93e7'

OLD_CONTEXT = 'Со сменой собственника предприятие вернет свое историческое название — «Хромпик»'
NEW_CONTEXT = OLD_CONTEXT + (
    '. Более 60 млрд рублей планируется вложить до конца 2026 года в '
    'модернизацию АО «Хромпик» — реализация программы стала возможна '
    'благодаря вхождению завода в ГК «Полипласт». По итогам '
    'модернизации выпуск продукции увеличен более чем в три раза, '
    'восстановлен основной сортамент, освоены новые рынки сбыта; '
    'штатная численность выросла на 65%, зарплата — вдвое. Новая '
    'технология позволила снизить выход шлама на 23% и практически в '
    '50 раз сократить потери шестивалентного хрома.')

NEW_SRCS = [
    ['Бизнес-журнал Урал', 'https://ural.business-magazine.online/'
     'fn_1688599.html'],
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/6212247'],
]


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в базе' % CARD_ID
    assert card['eco'].get('context') == OLD_CONTEXT, (
        'eco.context изменился с ожидаемого: %r' % card['eco'].get('context'))
    src = card.setdefault('src', [])
    print('ПРАВИМ  %s: eco.context — инвестпрограмма и итоги модернизации' % CARD_ID)
    if write:
        card['eco']['context'] = NEW_CONTEXT
        for s in NEW_SRCS:
            if s not in src:
                src.append(s)
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('ЗАПИСАНО')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
