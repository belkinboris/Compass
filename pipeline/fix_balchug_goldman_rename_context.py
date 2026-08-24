# -*- coding: utf-8 -*-
"""Месячная очередь, карточка gaa82c6f6 (Balchug Capital/«Голдман Сакс
Банк»): дельта-поиск нашёл, что случилось с банком ПОСЛЕ сделки — он
переименован в «Ориджин Банк» (ЕГРЮЛ, 18 июля 2025 года), лицензия
сохранена. Не через `review.py`: источник (bosfera.ru) не образует с
уже записанным текстом `eco.context` (про единственную банковскую
лицензию, из другого источника) непрерывный кусок.

Источник — читал напрямую (WebFetch, дословная цитата подтверждена;
также закэширован fetch_article_texts.py):
https://bosfera.ru/press-release/goldman-saks-bank-smenil-nazvanie-na-oridzhin-bank

Запуск: python3 pipeline/fix_balchug_goldman_rename_context.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gaa82c6f6'

OLD_CONTEXT = (
    'На начало 2025 г. у российского банка действует только одна '
    'лицензия – банковская, позволяющая осуществлять операции со '
    'средствами в рублях и иностранной валюте без права привлечения '
    'средств физлиц.'
)
CONTEXT_ADDITION = (
    ' Голдман Сакс Банк сменил название на Ориджин Банк — об этом '
    'свидетельствуют данные ЕГРЮЛ от 18 июля 2025 года. Компания '
    'Balchug Capital сообщала в пресс-релизе, что банк выкуплен с '
    'текущей лицензией, но продолжит работу под новым названием.'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"

    print(f'{CARD_ID} eco.context: += переименование в «Ориджин Банк» '
          f'после сделки')

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('ЗАПИСАНО')
    else:
        print('Сухой прогон. Запись — с --write.')


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
