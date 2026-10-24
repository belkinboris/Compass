# -*- coding: utf-8 -*-
"""Штамп второго чтения для g1a2f9d60 (аукцион торговых рядов в Нерехте,
15 млн рублей, static/data/pending.json): прочитана карточка целиком,
источник (data/inbox/raw/2026-10-24-articles.jsonl) целиком, механика
(`accept_card.findings`) пуста. Единственный найденный дефект — заголовок,
дословно скопированный из meta <title> источника, — уже исправлен
`pipeline/fix_g1a2f9d60_title_2026_10_24.py --write`.

Формат штампа — как у `second_reading.py` (`card[STAMP] = day`) и как у
соседней карточки той же серии g896a22ba (`"second_read": "2026-10-23"`).

Без ключа — сухой прогон, запись по --write.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
sys.path.insert(0, os.path.join(HERE, 'ingest'))
sys.path.insert(0, ROOT)

import accept_card  # noqa: E402

CARD_ID = 'g1a2f9d60'
DAY = '2026-10-24'


def main():
    write = '--write' in sys.argv
    base, pending = accept_card.load()
    card, where = accept_card.find_card(CARD_ID, base, pending)
    assert card is not None, '%s: карточки нет ни в базе, ни в очереди' % CARD_ID
    assert card.get('second_read') is None, card.get('second_read')
    card['second_read'] = DAY
    print('%s (%s): second_read -> %r' % (CARD_ID, where, DAY))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    accept_card.save(base, pending)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
