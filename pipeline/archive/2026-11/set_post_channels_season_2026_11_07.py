# -*- coding: utf-8 -*-
"""Пост «Сезона» (gfd435463, торговая галерея в здании Four Seasons) — в оба канала.

Владелец, 7 ноября 2026, на черновик «В КАНАЛ «Компас - Недвижимость»»: «Давай опубликуем
и в недвижимости и в основном». Правило channels.channels_for дает только канал
недвижимости (сумма не раскрыта), поэтому карточке ставится `post_channels` — поле,
которое главнее правила. Карточка еще в очереди (pending.json).

    python3 pipeline/archive/2026-11/set_post_channels_season_2026_11_07.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
CID = 'gfd435463'


def apply(data):
    card = next(c for c in data['cards'] if c['id'] == CID)
    assert 'Сезон' in card['title'], card['title']
    assert not card.get('post_channels'), card.get('post_channels')
    card['post_channels'] = ['main', 'realty']


def main(write):
    data = json.load(open(PENDING, encoding='utf-8'))
    apply(data)
    print('%s: post_channels = main, realty' % CID)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    data = json.load(open(PENDING, encoding='utf-8'))
    apply(data)
    with open(PENDING, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv[1:]))
