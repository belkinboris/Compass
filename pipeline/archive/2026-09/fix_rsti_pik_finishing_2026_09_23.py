# -*- coding: utf-8 -*-
"""Приток 23 сентября 2026, карточка g69c83a3f: убрана пресс-ссылка «в
статье» из law.struct (мета-отсылка к самому источнику вместо факта),
продавец привязан к существующему профилю «ГК ПИК».

Запуск: python3 pipeline/fix_rsti_pik_finishing_2026_09_23.py --write
"""
import argparse
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')

CARD_ID = 'g69c83a3f'
SELLER_PROFILE = 'gkpik'

OLD_STRUCT = (
    'Компания РСТИ подписала предварительный договор с ПИК и уже внесла задаток. '
    'Стоимость сделки составит около 8 миллиардов рублей, говорится в статье. Как '
    'указывается в ней, речь идет об участке площадью 5,3 гектара.'
)
NEW_STRUCT = (
    'Компания РСТИ подписала предварительный договор с ПИК и уже внесла задаток. '
    'Стоимость сделки составит около 8 миллиардов рублей, речь идет об участке '
    'площадью 5,3 гектара.'
)


def main(write):
    data = json.load(open(PENDING, encoding='utf-8'))
    card = next(c for c in data['cards'] if c['id'] == CARD_ID)
    assert card['law']['struct'] == OLD_STRUCT
    card['law']['struct'] = NEW_STRUCT
    assert card.get('seller_id') is None
    card['seller_id'] = SELLER_PROFILE
    if write:
        json.dump(data, open(PENDING, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('Записано: law.struct очищен, продавец -> %s.' % SELLER_PROFILE)
    else:
        print('Сухой прогон (--write, чтобы записать).')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--write', action='store_true')
    main(p.parse_args().write)
