# -*- coding: utf-8 -*-
"""Приёмка карточки g2b1ff5cb («Норникель» и БЕЛАЗ создают СП, 2026-09-11,
приток 15:20 МСК) — карточка несла `type: "M&A"`, хотя это создание
совместного предприятия (уже отмечено темой «Создание СП»), и не называла
предмет ни текстом, ни профилем: у обеих сторон нет продавца/покупателя —
это партнёрство, а не покупка. `asset` заполняется описанием самого СП по
тому же образцу, что уже применён к другим карточкам этого типа
(`gaa603e6d`, `gmru-geotek-bashneftegeofizika`) — состав и предмет
партнёрства, без выдумки.

Запуск: python3 pipeline/fix_nornikel_belaz_jv_type_asset.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g2b1ff5cb'
ASSET_TEXT = ('Совместное предприятие «Норникеля» и БЕЛАЗа для разработки '
              'и производства подземной горной техники (на первом этапе — '
              'ремонт и восстановление машин)')


def main(write=False):
    with open(BASE_PATH, encoding='utf-8') as f:
        base = json.load(f)

    card = next((c for c in base['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, 'карточка %s не найдена' % CARD_ID
    assert card['type'] == 'M&A', 'type уже другой'
    assert card.get('asset') is None, 'asset уже проставлен'

    card['type'] = 'Создание СП'
    card['asset'] = ASSET_TEXT

    print('Правка %s: type=Создание СП, asset дописан.' % CARD_ID)

    if write:
        with open(BASE_PATH, 'w', encoding='utf-8') as f:
            json.dump(base, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Записано.')
    else:
        print('(сухой прогон, для записи — --write)')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
