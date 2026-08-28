# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g69a22dab (Структура Умара
Кремлёва приобрела «Рольф» у Росимущества): дельта-поиск нашёл финансовую
судьбу дилера после сделки — растущий долг привёл к убытку в 2025 году.
Цитаты подтверждены лично прямым WebFetch.

За первое полугодие 2025 года «Рольф» получил чистый убыток по МСФО 5
млрд руб. — «расходы на выплаты по кредитам и займам подскочили в 2,6
раза, до 5,8 млрд руб.» (Интерфакс). По предварительным итогам всего 2025
года выручка составила 245 млрд руб., EBITDA снизилась на 8%, до 8,6 млрд
руб., при этом продажи новых автомобилей выросли на 14% — до 37,5 тыс.
единиц; с 2026 года компания стала официальным дилером Li Auto
(официальный сайт «Рольфа»).

Президентское согласование сделки, держателя залога по договору купли-
продажи (заложен АО «Автотех» в августе 2024) и консультантов сделки
дельта-поиск не нашёл ни в одном источнике — честная пустота, не тронуто.

Запуск: python3 pipeline/fix_kremlev_rolf_postdeal_financials.py
        python3 pipeline/fix_kremlev_rolf_postdeal_financials.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g69a22dab'

OLD_CONTEXT = (
    '«Рольф» — крупнейший автодилер в России, он был основан в 1991-м. '
    'До 2022-го портфель брендов «Рольфа» включал 21 марку автомобилей и '
    'один мотоциклетный бренд. В Москве и Санкт-Петербурге дилерская сеть '
    'компании насчитывала 62 шоурума.'
)
CONTEXT_ADDITION = (
    ' Под новым владельцем финансовое положение дилера ухудшилось: за '
    'первое полугодие 2025 года «Рольф» получил чистый убыток по МСФО 5 '
    'млрд руб. — «расходы на выплаты по кредитам и займам подскочили в '
    '2,6 раза, до 5,8 млрд руб.» (Интерфакс). По предварительным итогам '
    'всего 2025 года выручка ГК «РОЛЬФ» составила 245 млрд руб., EBITDA '
    'снизилась на 8%, до 8,6 млрд руб., хотя продажи новых автомобилей '
    'выросли на 14%, до 37,5 тыс. единиц; с 2026 года компания стала '
    'официальным дилером Li Auto (rolf.ru).'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['Интерфакс', 'https://www.interfax.ru/business/1045115'],
    ['РОЛЬФ', 'https://www.rolf.ru/news/rolf-podvel-predvaritelnye-itogi-2025-goda-i-predstavil-strategiyu-razvitiya-do-2030-goda/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
