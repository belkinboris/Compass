# -*- coding: utf-8 -*-
"""Пять карточек передачи активов во временное управление «Центр
Капиталу» (`build_centr_kapital_decree_2026_10_16.py`) собраны без
`buyer_name` — упущение сборки. Управляющий — текстом, без профиля,
как у прецедента Metro/«УК Торг РУС» (ga142d8e0): управляющая компания
без собственного бизнеса, профиль заводить не на что.

Запуск:
    python3 pipeline/fix_centr_kapital_buyer_name_2026_10_16.py            # сухой прогон
    python3 pipeline/fix_centr_kapital_buyer_name_2026_10_16.py --write    # применить
"""
import json
import sys

PENDING = '/home/user/Compass/static/data/pending.json'
CARD_IDS = ('g8a599c40', 'g19410fc2', 'gb3837d4d', 'gfc3e1ae2', 'gf803c055')
BUYER_NAME = '«Центр Капитал»'


def main(write=False):
    data = json.load(open(PENDING, encoding='utf-8'))
    cards = {c['id']: c for c in data['cards']}
    for cid in CARD_IDS:
        card = cards[cid]
        assert card.get('buyer_name') is None, '%s: buyer_name уже не пуст: %r' % (cid, card.get('buyer_name'))
        print('%s: buyer_name <- %r' % (cid, BUYER_NAME))
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh = json.load(open(PENDING, encoding='utf-8'))
    fresh_cards = {c['id']: c for c in fresh['cards']}
    for cid in CARD_IDS:
        fc = fresh_cards[cid]
        assert fc.get('buyer_name') is None, '%s: buyer_name поменяли параллельно — перечитайте' % cid
        fc['buyer_name'] = BUYER_NAME
    json.dump(fresh, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
