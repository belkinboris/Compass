# -*- coding: utf-8 -*-
"""Карточка `gc55152ad` («Книгу о Гарри Поттере с ошибками продали на
аукционе за 400 тысяч долларов», ПРАЙМ) дошла до pending.json через
resolve_duplicates.py (ответ `separate` на ложное совпадение с
`gd76643b6` — «Один из первых планов Москвы продали на торгах за
400 тыс. рублей», совпадение только по числу «400» и слову «продал»,
тот же класс, что уже несколько раз обсуждался в KNOWN_ISSUES.md 15
октября). Сама новость — зарубежный коллекционный аукцион (книга с
типографскими ошибками), ни одной российской стороны; парсинг дал
мусор: seller = «Книгу о Гарри Поттере с ошибками», asset = «на
аукционе».

Запуск:
    python3 pipeline/discard_gc55152ad_hp_book_not_russian_market_2026_10_15.py            # сухой прогон
    python3 pipeline/discard_gc55152ad_hp_book_not_russian_market_2026_10_15.py --write    # применить
"""
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
STATE = os.path.join(ROOT, 'data', 'inbox', 'moderation_state.json')

sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import promote  # noqa: E402

CARD_ID = 'gc55152ad'
URL = 'https://1prime.ru/20261015/independent-874307711.html'
TITLE_PART = 'Книгу о Гарри Поттере с ошибками'


def main(write=False):
    data = json.load(open(PENDING, encoding='utf-8'))
    card = next((c for c in data['cards'] if c['id'] == CARD_ID), None)
    if not card:
        print('НЕ ТРОГАЕМ %s — карточки уже нет в очереди' % CARD_ID)
        return 0
    if TITLE_PART not in str(card.get('title') or ''):
        print('НЕ ТРОГАЕМ %s — заголовок не совпадает: %r' % (CARD_ID, card.get('title')))
        return 1
    if card.get('draft_sent') or card.get('post_draft_sent'):
        print('НЕ ТРОГАЕМ %s — уже показана в консоли, решает человек' % CARD_ID)
        return 1
    print('ВЫКИДЫВАЕМ %s %s' % (CARD_ID, card['title']))
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    data['cards'] = [c for c in data['cards'] if c['id'] != CARD_ID]
    json.dump(data, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

    state = json.load(open(STATE, encoding='utf-8'))
    state.setdefault('discarded_urls', {})[URL] = {
        'id': CARD_ID,
        'title': card['title'],
        'at': datetime.now(timezone.utc).isoformat(),
        'note': 'не российский рынок: зарубежный коллекционный аукцион, ни одной российской стороны',
    }
    state.setdefault('raw_titles', {})[promote.raw_key(card['title'])] = 'auto-drop'
    json.dump(state, open(STATE, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено: карточка убрана, URL записан в discarded_urls.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
