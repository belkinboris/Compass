# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g1cc071e4 (Павел Харанек
приобретает Boosty и Donation Alerts у My.Games): дельта-поиск нашёл
официальное объявление My.Games о ЗАВЕРШЕНИИ продажи (11 декабря 2024
года, с задержкой на квартал против анонсированного закрытия в III
квартале 2024) и структуру владения после сделки — нидерландская CEBC
B.V. (принадлежит Харанеке), операционно бренды работают через
гонконгскую Zaya Solutions Limited, на которую в России зарегистрированы
товарные знаки Boosty и Donation Alerts. Признаков повторной продажи или
кризиса собственности за полтора года не найдено — платформа продолжает
работать. Дата сделки уточнена на дату официального закрытия. Не через
review.py: комбинация фактов из ДВУХ новых источников (my.games,
boosty.to) в структурных полях.

Запуск: python3 pipeline/fix_boosty_harkaneka_closed.py
        python3 pipeline/fix_boosty_harkaneka_closed.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g1cc071e4'

OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Закрыта'

OLD_DATE = '2024-08-15'
NEW_DATE = '2024-12-11'

OLD_CONTEXT = (
    'Покупатель — основатель Broadsmart Group. Компания занимается '
    'проектированием, дизайном и продвижением элитных жилых комплексов.'
)
CONTEXT_ADDITION = (
    ' My.Games официально объявила о завершении сделки 11 декабря 2024 '
    'года — с задержкой на квартал против анонсированного закрытия в '
    'III квартале 2024. Активы перешли нидерландской CEBC B.V., '
    'принадлежащей Харанеке; операционно платформы работают через '
    'гонконгскую Zaya Solutions Limited (зарегистрирована 6 февраля '
    '2025 года), на которую в России зарегистрированы товарные знаки '
    'Boosty и Donation Alerts. За полтора года после сделки платформа '
    'продолжает работать без признаков повторной продажи.'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['about.my.games', 'https://about.my.games/news/300'],
    ['boosty.to', 'https://boosty.to/langart/posts/e586b1cc-b194-4205-90b9-6bba5ccb9de1'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['status'] == OLD_STATUS
    assert deal['date'] == OLD_DATE
    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== status ===', NEW_STATUS)
    print('=== date ===', NEW_DATE)
    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['status'] = NEW_STATUS
        deal['date'] = NEW_DATE
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
