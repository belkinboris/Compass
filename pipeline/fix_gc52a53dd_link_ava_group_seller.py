# -*- coding: utf-8 -*-
"""Приток 8 сентября 2026 (12:20 МСК) — карточка gc52a53dd (пока в
очереди предпросмотра, static/data/pending.json): поле `seller` только
что исправлено через review.py на «AVA Group» (реальный продавец актива
в Приморском районе Петербурга), а профиль этой компании уже есть в базе
(ge6453621). `seller_id` не проходит через дословную проверку review.py
(это ссылка, а не цитата), поэтому связывается отдельным одноразовым
скриптом — тот же приём, что `link_named_parties_to_existing_profiles.py`.

Запуск: python3 pipeline/fix_gc52a53dd_link_ava_group_seller.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PENDING_PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')

CARD_ID = 'gc52a53dd'
COMPANY_ID = 'ge6453621'


def main(write=False):
    with open(DATA_PATH, encoding='utf-8') as f:
        data = json.load(f)
    with open(PENDING_PATH, encoding='utf-8') as f:
        pending = json.load(f)

    assert COMPANY_ID in data['companies'], f'профиля {COMPANY_ID} нет в базе'
    assert data['companies'][COMPANY_ID]['name'] == 'AVA Group'

    matches = [c for c in pending['cards'] if c['id'] == CARD_ID]
    assert len(matches) == 1, f'ожидалась ровно одна карточка {CARD_ID} в очереди предпросмотра, найдено {len(matches)}'
    card = matches[0]
    assert card.get('seller') == 'AVA Group', f'ожидали seller="AVA Group", нашли {card.get("seller")!r}'
    assert not card.get('seller_id'), f'seller_id уже стоит: {card.get("seller_id")!r}'

    card['seller_id'] = COMPANY_ID
    if card.get('seller_src') == 'text':
        del card['seller_src']

    print(f'{CARD_ID}: seller_id -> {COMPANY_ID} (AVA Group)')

    if write:
        with open(PENDING_PATH, 'w', encoding='utf-8') as f:
            json.dump(pending, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Записано.')
    else:
        print('(сухой прогон, для записи — --write)')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
