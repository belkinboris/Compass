# -*- coding: utf-8 -*-
"""Карточка g7bff6e5c: `asset` нёс конкретную долю (12,5%) и оценку
(1,6 млрд руб.) как будто это подтверждённые условия закрытия, хотя
источник о закрытии (Ведомости) эти цифры не называет вовсе — они из
анонса раунда (ComNews, июль 2025). Находка второго чтения: сумма могла
не измениться, но доля и оценка — не факт. Снимает долю/оценку из
`asset` до общей формулировки; подробности с явной оговоркой «при
объявлении» остаются в eco.share/eco.val (отдельная консолидация).

Запуск:
    python3 pipeline/fix_visiology_asset_v2_2026_10_16.py            # сухой прогон
    python3 pipeline/fix_visiology_asset_v2_2026_10_16.py --write    # применить
"""
import json
import sys

PENDING = '/home/user/Compass/static/data/pending.json'
CARD_ID = 'g7bff6e5c'
OLD_ASSET = '12,5% капитала АО «Визиолоджи» (допэмиссия)'
NEW_ASSET = 'допэмиссия акций АО «Визиолоджи»'


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
