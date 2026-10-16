# -*- coding: utf-8 -*-
"""Новая карточка: Фонд развития территорий выставил на торги недостроенный
ЖК «Шлиссельбургский дворик» в Шлиссельбурге (Ленобласть) — два корпуса
готовностью 15% и 62% общей площадью 39,1 тыс. кв. м плюс арендные права
на два участка 1,8 га. Аукцион голландский (с понижением), площадка РАД
Lot-online.ru, торги 12 ноября, заявки до 6 ноября; стартовая цена
161,8 млн ₽, нижняя планка 64,7 млн ₽. Покупатель пока не определён —
статус «Обсуждается» (прецедент того же класса — g955d2c6b, недострой в
Кургане).

Единственный источник на момент сборки — dp.ru.

Запуск:
    python3 pipeline/build_shlisselburg_dolgostroy_2026_10_16.py            # сухой прогон
    python3 pipeline/build_shlisselburg_dolgostroy_2026_10_16.py --write    # применить
"""
import json
import os
import sys
from datetime import datetime, timezone

ROOT = '/home/user/Compass'
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import promote  # noqa: E402

PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

SRC = ['Деловой Петербург', 'https://www.dp.ru/a/2026/10/16/dolgostroj-v-shlisselburge']

DRAFT = {
    'date': '2026-10-16',
    'title': 'Фонд развития территорий выставил на торги недострой «Шлиссельбургский дворик»',
    'ind': 'Недвижимость',
    'type': 'Продажа с торгов',
    'status': 'Обсуждается',
    'src': [SRC],
    'seller': 'Фонд развития территорий',
    'asset': 'недостроенный ЖК «Шлиссельбургский дворик» в Шлиссельбурге (два корпуса '
             'общей площадью 39,1 тыс. кв. м и арендные права на два участка 1,8 га)',
    'sum': '161,8 млн ₽',
    'events': [{
        'kind': 'approval',
        'date': '2026-10-16',
        'title': 'Объявлены торги',
        'note': 'Аукцион проведёт площадка РАД Lot-online.ru 12 ноября 2026 года, '
                'заявки принимаются до 6 ноября; схема — голландская (с понижением), '
                'стартовая цена 161,8 млн ₽, нижняя планка 64,7 млн ₽.',
        'source': SRC,
    }],
}


def main(write=False):
    pending = json.load(open(PENDING, encoding='utf-8'))
    promoted = json.load(open(DATA, encoding='utf-8'))
    existing_ids = {c['id'] for c in pending['cards']} | {d['id'] for d in promoted['deals']}
    if any('Шлиссельбургский дворик' in (c.get('title') or '') for c in pending['cards']):
        print('ОТКАЗ: похожая карточка уже в pending.json')
        return 1

    card_id = promote.new_id(existing_ids)
    card = promote.to_card(DRAFT, card_id)
    card['pending_since'] = datetime.now(timezone.utc).isoformat()

    print('НОВАЯ КАРТОЧКА %s: %s' % (card_id, card['title']))
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh = json.load(open(PENDING, encoding='utf-8'))
    if any(c['id'] == card_id for c in fresh['cards']):
        print('ОТКАЗ: id уже занят — перечитайте и повторите')
        return 1
    fresh['cards'].append(card)
    json.dump(fresh, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
