# -*- coding: utf-8 -*-
"""Карточка g7bff6e5c (Visiology, раунд на платформе «Поток») собрана без
`asset` — предмет сделки (допэмиссия 12,5% капитала) был только в
`eco.share`, в косвенном падеже, и попадал в строку «Предмет» поста как
есть (находка accept_card.py: «косвенный падеж вместо именительного»).
Задаёт `asset` именительным падежом.

Запуск:
    python3 pipeline/fix_visiology_asset_2026_10_16.py            # сухой прогон
    python3 pipeline/fix_visiology_asset_2026_10_16.py --write    # применить
"""
import json
import sys

PENDING = '/home/user/Compass/static/data/pending.json'
CARD_ID = 'g7bff6e5c'
ASSET = '12,5% капитала АО «Визиолоджи» (допэмиссия)'


def main(write=False):
    data = json.load(open(PENDING, encoding='utf-8'))
    card = {c['id']: c for c in data['cards']}[CARD_ID]
    assert card.get('asset') is None, 'asset уже не пуст: %r' % card.get('asset')
    print('%s: asset <- %r' % (CARD_ID, ASSET))
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh = json.load(open(PENDING, encoding='utf-8'))
    fc = {c['id']: c for c in fresh['cards']}[CARD_ID]
    assert fc.get('asset') is None, 'asset поменяли параллельно — перечитайте'
    fc['asset'] = ASSET
    json.dump(fresh, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
