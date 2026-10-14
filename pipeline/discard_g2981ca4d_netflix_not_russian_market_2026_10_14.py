# -*- coding: utf-8 -*-
"""Ворота пропустили «Netflix приобрел права на трансляцию матчей ЧМ-2030
по футболу» (`g2981ca4d`) — предмет в заголовке оказался кириллицей
(«права на трансляцию...»), и это замаскировало то, что у истории нет
НИ ОДНОГО признака российского рынка: американский стриминг купил права
на трансляцию чемпионата мира (Испания/Португалия/Марокко), источник —
пересказ Коммерсанта в разделе зарубежных новостей, сумма не раскрыта,
ни одной российской стороны. Такая же находка уже отсеивалась раз-отказом
в `raw_screen.py` (BlackRock, Hyundai/Индия) — здесь гейт её не поймал,
потому что ЦЕЛЬ (не покупатель) была названа по-русски.

Действие — то же самое, что кнопка «🗑 Выкинуть»: карточка убирается из
`pending.json`, URL — в `discarded_urls`, черновик — `decided_raw[...]=
'auto-drop'` и `raw_titles`.

Запуск:
    python3 pipeline/discard_g2981ca4d_netflix_not_russian_market_2026_10_14.py            # сухой прогон
    python3 pipeline/discard_g2981ca4d_netflix_not_russian_market_2026_10_14.py --write    # применить
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

CARD_ID = 'g2981ca4d'
URL = 'https://www.kommersant.ru/doc/9026381'
TITLE_PART = 'Netflix приобрел права на трансляцию матчей ЧМ-2030'


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
        'note': 'не российский рынок: американский Netflix купил права на трансляцию ЧМ-2030 '
                '(Испания/Португалия/Марокко), ни одной российской стороны',
    }
    state.setdefault('decided_raw', {})
    state.setdefault('raw_titles', {})[promote.raw_key(card['title'])] = 'auto-drop'
    json.dump(state, open(STATE, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено: карточка убрана, URL записан в discarded_urls.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
