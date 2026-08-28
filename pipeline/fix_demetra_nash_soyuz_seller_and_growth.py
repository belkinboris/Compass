# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка gc10da566 (Деметра-холдинг
приобрел элеватор ООО «Наш Союз» в Орловской области, октябрь 2024):
дельта-поиск нашёл продавца и рост отгрузок после сделки, оба факта
подтверждены лично прямым WebFetch.

1. Продавец — по данным ЕГРЮЛ (audit-it.ru): «Цуканов Владислав
   Владимирович больше не числится в ЕГРЮЛ учредителем» с датой смены
   16.10.2024, «Новый учредитель – ООО «ДЕМЕТРА ТРЕЙДИНГ»». Поле `seller`
   было пустым.
2. Рост отгрузок после сделки (vechor.ru): элеватор «Наш Союз» в 4
   квартале 2024 года отгрузил 36 тыс. тонн зерна — на 71% больше того же
   периода годом ранее; все элеваторы «Деметра-Холдинг» в 2024 году
   отгрузили 1,18 млн тонн — на треть больше показателей 2023 года.
   `eco.context` был прочерком.

Сумма сделки и консультанты по-прежнему не раскрыты ни в одном найденном
источнике. Не через review.py: факты из НОВЫХ источников для двух разных
полей.

Запуск: python3 pipeline/fix_demetra_nash_soyuz_seller_and_growth.py
        python3 pipeline/fix_demetra_nash_soyuz_seller_and_growth.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gc10da566'

OLD_SELLER = None
NEW_SELLER = 'Владислав Цуканов'

OLD_CONTEXT = '—'
NEW_CONTEXT = (
    'После сделки отгрузки элеватора выросли: в четвёртом квартале 2024 '
    'года «Наш Союз» отгрузил на железнодорожный транспорт 36 тыс. тонн '
    'зерна — «на 71% превосходит показатели того же периода предыдущего '
    'года». Все элеваторы «Деметра-Холдинг» в 2024 году отгрузили 1,18 '
    'млн тонн зерна — «на треть выше показателей 2023 года» (vechor.ru).'
)

NEW_SRC = [
    ['Audit-it.ru', 'https://www.audit-it.ru/contragent/1145749002310_ooo-nash-soyuz'],
    ['Вечор', 'https://vechor.ru/economy/verkhovskij-elevator-na-70-uvelichil-otgruzku-zerna'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal.get('seller') == OLD_SELLER
    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== seller: станет ===')
    print(NEW_SELLER)
    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['seller'] = NEW_SELLER
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
