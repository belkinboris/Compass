# -*- coding: utf-8 -*-
"""Новая карточка: «РТ-Капитал» (непрофильные активы «Ростеха») выставила
на торги комплекс зданий бывшего МРТИ РАН на Варшавском шоссе в Москве.
Тот же тип сделки и организатор, что у уже закрытой карточки ge957fc7b
(«Ростех»/«Швабе»/Клебанов) — лот продаётся не напрямую недвижимостью, а
через 100% уставного капитала АО «МРТИ РАН», как и у прежнего прецедента
gb4ebeacf (ВИЛС).

Источник (прочитан полностью, кэш data/inbox/raw/2026-10-13-articles.jsonl):
  РИА Недвижимость  https://realty.ria.ru/20261013/rt-kapital-2124124441.html

Торги назначены на 9 ноября 2026 — исхода пока нет, статус «Обсуждается».

Запуск:
    python3 build_mrti_ran_2026_10_13.py            # сухой прогон
    python3 build_mrti_ran_2026_10_13.py --write    # применить
"""
import json
import os
import sys
from datetime import datetime, timezone

ROOT = '/home/user/Compass'
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import promote  # noqa: E402

PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')

CARD_ID = 'g6c1f9d4e'
SRC = ['РИА Недвижимость', 'https://realty.ria.ru/20261013/rt-kapital-2124124441.html']

DRAFT = {
    'id': CARD_ID,
    'date': '2026-10-13',
    'title': '«РТ-Капитал» выставила на торги комплекс зданий бывшего НИИ радиотехники РАН на Варшавском шоссе',
    'ind': 'Недвижимость',
    'type': 'Продажа с торгов',
    'status': 'Обсуждается',
    'src': [SRC],
    'seller': '«Ростех»',
    'asset': 'здания Московского радиотехнического института РАН (АО «МРТИ РАН») на Варшавском шоссе',
}


def main(write=False):
    data = json.load(open(PENDING, encoding='utf-8'))
    if any(c['id'] == CARD_ID for c in data['cards']):
        print('ОТКАЗ: карточка %s уже есть' % CARD_ID)
        return 1

    card = promote.to_card(DRAFT, CARD_ID)
    card['seller_id'] = 'g7802e51e'  # Ростех
    card['sum'] = '10,2 млрд ₽'
    card['sum_basis'] = 'auction_start'
    card['eco']['sum'] = '10,2 млрд ₽ (начальная цена торгов)'
    card['eco']['share'] = (
        'В лот входят 11 зданий и два нежилых помещения на Варшавском шоссе, 132 — почти '
        '94 тыс. кв. м в сумме, — а также права на 12 участков земли общей площадью '
        '9,1 гектара.'
    )
    card['law']['struct'] = (
        'Актив продаётся не как недвижимость напрямую, а через 100% доли в уставном '
        'капитале АО «МРТИ РАН», на балансе которого здания и находятся. Организатор '
        'торгов — «РТ-Капитал», которая занимается непрофильными активами «Ростеха». '
        'Торги намечены на 9 ноября 2026 года.'
    )
    card['party_evidence'] = {
        'seller': [{'value': 'Ростех', 'field': 'seller', 'method': 'explicit_news_title', 'url': SRC[1]}],
        'target': [{'value': DRAFT['asset'], 'field': 'asset', 'method': 'explicit_news_title', 'url': SRC[1]}],
    }
    card['themes'] = ['Продажа с торгов']
    card['pending_since'] = datetime.now(timezone.utc).isoformat()
    card['events'] = [{
        'id': 'negotiations-2026-10-13', 'kind': 'negotiations', 'date': '2026-10-13',
        'title': 'Переговоры', 'historicalTitle': DRAFT['title'], 'note': '',
        'sources': [SRC],
    }]

    print('НОВАЯ КАРТОЧКА %s: %s' % (CARD_ID, card['title']))
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh = json.load(open(PENDING, encoding='utf-8'))
    if any(c['id'] == CARD_ID for c in fresh['cards']):
        print('ОТКАЗ: карточка уже появилась между чтением и записью')
        return 1
    fresh['cards'].append(card)
    json.dump(fresh, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
