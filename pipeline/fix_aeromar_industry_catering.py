# -*- coding: utf-8 -*-
"""«Аэромар» — бортовое питание, а не транспорт: отрасль карточек.

ЗАЧЕМ. Партнёр (K+, 7 сентября 2026) о посте «Аэрофлот выкупил долю
структуры Lufthansa в «Аэромаре»» с тегом #Транспортилогистика: «вот это ещё
ритейл, потому что это кейтеринговый бизнес». Отрасль карточке досталась от
покупателя (авиакомпания), а не от предмета: «Аэромар» производит бортовое
питание — это пищепром. Транспорт остаётся второй отраслью (заказчики —
авиакомпании), чтобы сделка по-прежнему находилась в подборке по транспорту.

Две карточки одной истории: намерение (g42e42759) и закрытие (g2c27516d).
Опубликованный пост канала (71) не трогаем — правило владельца.

Запуск:
    python3 pipeline/fix_aeromar_industry_catering.py           # сухой прогон
    python3 pipeline/fix_aeromar_industry_catering.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
IDS = ('g42e42759', 'g2c27516d')
NEW_IND = 'Пищепром и напитки'
SECOND = 'Транспорт и логистика'


def main(write=False):
    base = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in base['deals']}
    for did in IDS:
        card = by_id[did]
        assert 'Аэромар' in (card.get('title') or ''), did
        if card.get('ind') == NEW_IND and card.get('industries') == [NEW_IND, SECOND]:
            print('%s: уже исправлена' % did)
            continue
        assert card.get('ind') == SECOND, (did, card.get('ind'))
        print('%s: %s -> %s (+ вторая отрасль %s)' % (did, card['ind'], NEW_IND, SECOND))
        card['ind'] = NEW_IND
        card['industries'] = [NEW_IND, SECOND]
    if write:
        json.dump(base, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('Записано.')
    else:
        print('Сухой прогон. Запись — с --write.')


if __name__ == '__main__':
    main('--write' in sys.argv)
