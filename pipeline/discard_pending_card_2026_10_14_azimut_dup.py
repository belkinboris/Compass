# -*- coding: utf-8 -*-
"""Ворота пропустили ЕЩЁ один дубль исхода аукциона «Azimut отель
Ярославль» — на этот раз через mergers.ru, заголовок «Azimut Hotels
выкупает гостиницу в Ярославле» (без цены, без даты итогов), статус
«Обсуждается». Сделка уже закрыта и полностью описана в `g39e9e9c2`
(361,9 млн ₽, покупатель — профиль Azimut Hotels, 9 октября 2026) — тот
же класс дефекта матчера, что уже чинился 13 октября (другой ракурс
заголовка, общих слов почти нет).

Действие — то же самое, что кнопка «🗑 Выкинуть»: карточка убирается из
`pending.json`, URL — в `discarded_urls`, черновик — `decided_raw[...]=
'auto-drop'` и `raw_titles`.

Запуск:
    python3 pipeline/discard_pending_card_2026_10_14_azimut_dup.py            # сухой прогон
    python3 pipeline/discard_pending_card_2026_10_14_azimut_dup.py --write    # применить
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

CARD_ID = 'gfd8a5d08'
URL = 'https://mergers.ru/news/Azimut-Hotels-vykupaet-gostinicu-v-Yaroslavle-87643'
TITLE_PART = 'Azimut Hotels выкупает гостиницу в Ярославле'


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
        'note': 'дубль уже закрытой сделки g39e9e9c2 (Azimut/Ярославль) через mergers.ru — матчер не связал заголовки',
    }
    state.setdefault('raw_titles', {})[promote.raw_key(card['title'])] = 'enrich:g39e9e9c2'
    json.dump(state, open(STATE, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено: карточка убрана, URL записан в discarded_urls.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
