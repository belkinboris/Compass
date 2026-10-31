# -*- coding: utf-8 -*-
"""Карточка gc04356ba («Сила Востока»/Нетчен-Хая): дата события events[0] не
подтянулась за правкой карточного `date` (review.py FIXES меняет поле `date`
верхнего уровня, но не умеет адресовать элемент списка `events[]` через
точечный путь) — второе чтение 29 октября 2026 уже перенесло `date` карточки
с 2026-10-29 на 2026-10-26 (торги прошли 26-го, 29-е — день позднейшей
републикации ПРАЙМ), а `events[0].date` и дата внутри `note` остались 29-м:
на сайте таймлайн сделки (dealEvents() в static/index.html) показал бы два
разных дня одного и того же события.

Запуск:
    python3 pipeline/fix_gc04356ba_closed_event_date.py            # сухой прогон
    python3 pipeline/fix_gc04356ba_closed_event_date.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PENDING = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'pending.json')

CARD_ID = 'gc04356ba'
OLD_DATE = '2026-10-29'
NEW_DATE = '2026-10-26'
OLD_NOTE = ('29 октября аукцион на участок рудного золота Нетчен-Хая в Магаданской области '
            'завершился победой компании «Сила Востока»: на 15-м шаге она предложила 1,125 '
            'млрд рублей при стартовом платеже 450 млн рублей — итоговая цена превысила '
            'стартовую в 2,5 раза.')
NEW_NOTE = ('26 октября аукцион на участок рудного золота Нетчен-Хая в Магаданской области '
            'завершился победой компании «Сила Востока»: на 15-м шаге она предложила 1,125 '
            'млрд рублей при стартовом платеже 450 млн рублей — итоговая цена превысила '
            'стартовую в 2,5 раза.')


def main():
    write = '--write' in sys.argv
    pending = json.load(open(PENDING, encoding='utf-8'))
    card = next((c for c in pending['cards'] if c.get('id') == CARD_ID), None)
    assert card is not None, '%s не найдена в pending.json' % CARD_ID
    events = card.get('events') or []
    assert len(events) == 1, 'ожидался один events[] у %s, нашлось %d' % (CARD_ID, len(events))
    ev = events[0]
    assert ev.get('date') == OLD_DATE, 'events[0].date уже другое: %r' % ev.get('date')
    assert ev.get('note') == OLD_NOTE, 'events[0].note уже другой'
    print('ПРАВИМ %s events[0].date %r -> %r' % (CARD_ID, OLD_DATE, NEW_DATE))
    if write:
        ev['date'] = NEW_DATE
        ev['note'] = NEW_NOTE
        json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('Записано.')
    else:
        print('Сухой прогон. Запись — с ключом --write.')


if __name__ == '__main__':
    main()
