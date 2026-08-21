# -*- coding: utf-8 -*-
"""Wildberries & Russ/«Рив Гош» (`g94683ed2`): месячный дообыск нашёл
поздний факт о ходе интеграции — рост спроса на товары «Рив Гош» после
присоединения к экосистеме Wildberries, подтверждённый президентом
группы компаний Эдгаром Шабановым (интервью «Газете.Ru», 4 февраля
2026). Записано как событие `events[]`, не полем лога — это конкретная,
датированная новость, а не переформулировка уже известного факта о
структуре сделки.

Запуск: python3 pipeline/fix_rivgosh_wb_integration_event.py           # проверка
        python3 pipeline/fix_rivgosh_wb_integration_event.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g94683ed2'
NEW_EVENT = {
    'kind': 'other',
    'date': '2026-02-04',
    'title': 'Рост спроса на товары «Рив Гош» после интеграции с Wildberries',
    'note': ('После присоединения к экосистеме Wildberries & Russ '
             'сеть «Рив Гош» зафиксировала рост спроса на свою '
             'продукцию по всем ключевым бьюти-категориям, рассказал '
             'президент группы компаний Эдгар Шабанов в интервью '
             '«Газете.Ru». Существенный прирост заказов пришёлся на '
             'регионы, где у сети нет офлайн-магазинов, — прежде всего '
             'за счёт логистической инфраструктуры маркетплейса.'),
    'source': ['RB.ru', 'https://rb.ru/news/riv-gosh-fiksiruet-rost-'
               'prodazh-posle-integracii-s-wildberries-silnee-vsego-'
               'spros-uvelichilsya-v-regionah-rossii/'],
}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в базе' % CARD_ID
    assert not card.get('events'), 'events уже не пуст: %r' % card.get('events')
    print('ДОБАВИМ %s: events[] запись о росте спроса после интеграции' % CARD_ID)
    if write:
        card['events'] = [NEW_EVENT]
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('ЗАПИСАНО')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
