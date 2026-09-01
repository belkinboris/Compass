# -*- coding: utf-8 -*-
"""Сбербанк/Summit Towers (`g0ff8c5c4`, ещё в очереди предпросмотра):
подсказка review.py — `buyer_name` записан текстом «Сбербанк», хотя
профиль (`g28ff15bb`) уже есть в базе. Связывает `buyer` с профилем и
СНИМАЕТ `buyer_name` — иначе получится ровно тот дефект, что уже поймал
`test_buyer_is_named_once` на карточке Аэрофлот/Аэромар в этот же день
(имя покупателя показывалось бы дважды: текстом и через профиль).

Карточка ещё лежит в static/data/pending.json.

Запуск: python3 pipeline/fix_sberbank_summit_towers_link_buyer.py           # проверка
        python3 pipeline/fix_sberbank_summit_towers_link_buyer.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')

CARD_ID = 'g0ff8c5c4'
BUYER_ID = 'g28ff15bb'
BUYER_NAME = 'Сбербанк'


def main(write=False):
    data = json.load(open(PENDING, encoding='utf-8'))
    card = next((c for c in data['cards'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в pending.json' % CARD_ID
    assert card.get('buyer_name') == BUYER_NAME, 'buyer_name уже другое: %r' % card.get('buyer_name')
    assert card.get('buyer') is None, 'buyer уже связан: %r' % card.get('buyer')

    print('СВЯЗЫВАЮ buyer -> %s, снимаю buyer_name' % BUYER_ID)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 1

    card['buyer'] = BUYER_ID
    card.pop('buyer_name', None)
    json.dump(data, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv[1:]))
