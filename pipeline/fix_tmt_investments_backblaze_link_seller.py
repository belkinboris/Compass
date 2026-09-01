# -*- coding: utf-8 -*-
"""TMT Investments/Backblaze (`g0311444f`, ещё в очереди предпросмотра):
подсказка review.py — `seller` записан текстом «TMT Investments», хотя
профиль (`g5f515899`) уже есть в базе. Связывает `seller_id` с профилем
и снимает текстовое `seller` — тот же принцип, что и для `buyer`/
`buyer_name` (`test_buyer_is_named_once`), применённый к продавцу ради
единообразия, хоть отдельного теста на эту пару полей и нет.

Карточка ещё лежит в static/data/pending.json.

Запуск: python3 pipeline/fix_tmt_investments_backblaze_link_seller.py           # проверка
        python3 pipeline/fix_tmt_investments_backblaze_link_seller.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')

CARD_ID = 'g0311444f'
SELLER_ID = 'g5f515899'
SELLER_NAME = 'TMT Investments'


def main(write=False):
    data = json.load(open(PENDING, encoding='utf-8'))
    card = next((c for c in data['cards'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в pending.json' % CARD_ID
    assert card.get('seller') == SELLER_NAME, 'seller уже другое: %r' % card.get('seller')
    assert card.get('seller_id') is None, 'seller_id уже связан: %r' % card.get('seller_id')

    print('СВЯЗЫВАЮ seller_id -> %s, снимаю seller' % SELLER_ID)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 1

    card['seller_id'] = SELLER_ID
    card.pop('seller', None)
    json.dump(data, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv[1:]))
