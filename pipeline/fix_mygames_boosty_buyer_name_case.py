# -*- coding: utf-8 -*-
"""Правка вдогонку `fix_mygames_boosty_closed_not_vk.py`: `buyer_name`
карточки `gc6322659` начинался со слова «Структуры» — pymorphy уверенно
разбирает его как родительный падеж («структуры» кого-то), и
`test_party_name_is_in_the_nominative_case` справедливо это ловит (тот же
класс, что уже описан в CLAUDE.md для «Автодома»/«Виктору Маршеву»).
Переставлено: первым словом теперь «Broadsmart Group» (латиница, тест её
не разбирает), а «структуры Павла Харанеки» — поясняющая часть в скобках,
факт не меняется.

Запуск: python3 pipeline/fix_mygames_boosty_buyer_name_case.py
        python3 pipeline/fix_mygames_boosty_buyer_name_case.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gc6322659'
OLD_BUYER_NAME = 'Структуры Павла Харанеки (Broadsmart Group)'
NEW_BUYER_NAME = 'Broadsmart Group (структуры Павла Харанеки)'


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal.get('buyer_name') == OLD_BUYER_NAME

    print('=== buyer_name: станет ===')
    print(NEW_BUYER_NAME)

    if write:
        deal['buyer_name'] = NEW_BUYER_NAME
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
