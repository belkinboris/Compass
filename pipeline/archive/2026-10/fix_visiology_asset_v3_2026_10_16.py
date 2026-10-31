# -*- coding: utf-8 -*-
"""Карточка g7bff6e5c: пятый круг второго чтения нашел, что `asset`
(«допэмиссия акций АО «Визиолоджи»») называет механизм выпуска акций
словом «допэмиссия», которого нет ни в одном источнике — это домысленная
юридическая классификация (выведена из арифметики оценок, не из текста).
Снято до нейтрального «акции АО «Визиолоджи»» — источники прямо называют
акции (140 руб. за штуку), но не их юридический механизм.

Запуск:
    python3 pipeline/fix_visiology_asset_v3_2026_10_16.py            # сухой прогон
    python3 pipeline/fix_visiology_asset_v3_2026_10_16.py --write    # применить
"""
import json
import sys

PENDING = '/home/user/Compass/static/data/pending.json'
CARD_ID = 'g7bff6e5c'
OLD_ASSET = 'допэмиссия акций АО «Визиолоджи»'
NEW_ASSET = 'акции АО «Визиолоджи»'


def main(write=False):
    data = json.load(open(PENDING, encoding='utf-8'))
    card = {c['id']: c for c in data['cards']}[CARD_ID]
    assert card.get('asset') == OLD_ASSET, 'asset уже не тот: %r' % card.get('asset')
    print('%s: asset %r -> %r' % (CARD_ID, OLD_ASSET, NEW_ASSET))
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh = json.load(open(PENDING, encoding='utf-8'))
    fc = {c['id']: c for c in fresh['cards']}[CARD_ID]
    assert fc.get('asset') == OLD_ASSET, 'asset поменяли параллельно — перечитайте'
    fc['asset'] = NEW_ASSET
    json.dump(fresh, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
