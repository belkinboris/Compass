# -*- coding: utf-8 -*-
"""У карточки `cc41afead` («УГМК выкупает более 80% «Сусуманзолота» у
наследников основателя») нет структурной связи с покупателем, хотя профиль
УГМК уже есть в базе (`g3a8fb04f`) и заголовок называет его прямо.

Запуск: python3 pipeline/fill_frame_ugmk_susumanzoloto.py
        python3 pipeline/fill_frame_ugmk_susumanzoloto.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

CARD_ID = 'cc41afead'
BUYER_ID = 'g3a8fb04f'


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == CARD_ID)
    if card.get('buyer') == BUYER_ID:
        print('УЖЕ ПРИМЕНЕНО %s' % CARD_ID)
        return
    assert 'buyer' not in card, '%s: buyer уже задан' % CARD_ID
    print('ПРАВИМ  %s: buyer=%s (УГМК)' % (CARD_ID, BUYER_ID))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    card['buyer'] = BUYER_ID
    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
