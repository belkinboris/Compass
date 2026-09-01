# -*- coding: utf-8 -*-
"""Аэрофлот/Аэромар (`g2c27516d`, ещё в очереди предпросмотра): подсказка
review.py — `buyer_name` записан текстом, хотя профиль ПАО «Аэрофлот»
(`gf3ed02a1`) уже есть в базе. Профиль АО «Аэромар» (`g40580395`) тоже уже
есть и совпадает по имени с `asset`. Связывает оба текстовых поля с
существующими профилями — точное совпадение имени, без вхождения
подстрокой (тот же принцип, что `link_named_parties_to_existing_profiles.py`).

Карточка ещё лежит в static/data/pending.json (ворота её туда положили
сегодня), поэтому скрипт работает с pending.json, а не с базой.

Запуск: python3 pipeline/fix_aeroflot_aeromar_link_profiles.py           # проверка
        python3 pipeline/fix_aeroflot_aeromar_link_profiles.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')

CARD_ID = 'g2c27516d'
BUYER_ID = 'gf3ed02a1'
BUYER_NAME = '«Аэрофлот»'
TARGET_ID = 'g40580395'
ASSET = ('49% в «Аэромаре» — крупнейшей в России компании по производству '
         'бортового питания')


def main(write=False):
    data = json.load(open(PENDING, encoding='utf-8'))
    card = next((c for c in data['cards'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в pending.json' % CARD_ID
    assert card.get('buyer_name') == BUYER_NAME, 'buyer_name уже другое: %r' % card.get('buyer_name')
    assert card.get('buyer') is None, 'buyer уже связан: %r' % card.get('buyer')
    assert card.get('asset') == ASSET, 'asset уже другое: %r' % card.get('asset')
    assert card.get('target') is None, 'target уже связан: %r' % card.get('target')

    print('СВЯЗЫВАЮ buyer -> %s, target -> %s' % (BUYER_ID, TARGET_ID))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 1

    card['buyer'] = BUYER_ID
    card['target'] = TARGET_ID
    json.dump(data, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv[1:]))
