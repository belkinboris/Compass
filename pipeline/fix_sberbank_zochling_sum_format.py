# -*- coding: utf-8 -*-
"""У карточки `g5c3eeb06» («Сбербанк продал австрийскую дочку Sberbank
Europe AG Штефану Зочлингу») верхнеуровневое `sum` несло «240 млн €» —
значок валюты ПОСЛЕ числа, что нарушает принятый в базе формат («$ и €
перед числом», см. CLAUDE.md). Собственное `eco.sum` этой же карточки уже
записано верно — «€240 млн». Правится только порядок символов, значение не
меняется.

Запуск: python3 pipeline/fix_sberbank_zochling_sum_format.py
        python3 pipeline/fix_sberbank_zochling_sum_format.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g5c3eeb06'
OLD_SUM = '240 млн €'
NEW_SUM = '€240 млн'


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == CARD_ID)
    if card['sum'] == NEW_SUM:
        print('УЖЕ ПРИМЕНЕНО %s' % CARD_ID)
        return
    assert card['sum'] == OLD_SUM, '%s: sum уже другой' % CARD_ID
    print('ПРАВИМ  %s sum: «%s» -> «%s» (значок валюты перед числом)' % (CARD_ID, OLD_SUM, NEW_SUM))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    card['sum'] = NEW_SUM
    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
