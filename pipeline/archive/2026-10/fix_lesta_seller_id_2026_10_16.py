# -*- coding: utf-8 -*-
"""Карточка gd09e0945: seller="Росимущество" текстом, хотя в базе уже есть
профиль g9fd82fee ("Росимущество") — подсказка write_card.py после записи
прозы. Связывает seller_id с существующим профилем.

Запуск:
    python3 pipeline/fix_lesta_seller_id_2026_10_16.py            # сухой прогон
    python3 pipeline/fix_lesta_seller_id_2026_10_16.py --write    # применить
"""
import json
import sys

PENDING = '/home/user/Compass/static/data/pending.json'
CARD_ID = 'gd09e0945'
SELLER_ID = 'g9fd82fee'


def main(write=False):
    data = json.load(open(PENDING, encoding='utf-8'))
    cards = {c['id']: c for c in data['cards']}
    card = cards[CARD_ID]
    assert card.get('seller_id') is None, 'seller_id уже не пуст: %r' % card.get('seller_id')
    print('%s: seller_id <- %r' % (CARD_ID, SELLER_ID))
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh = json.load(open(PENDING, encoding='utf-8'))
    fc = {c['id']: c for c in fresh['cards']}[CARD_ID]
    assert fc.get('seller_id') is None, 'seller_id поменяли параллельно — перечитайте'
    fc['seller_id'] = SELLER_ID
    json.dump(fresh, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
