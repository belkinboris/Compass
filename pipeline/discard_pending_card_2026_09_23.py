# -*- coding: utf-8 -*-
"""Убрать из очереди предпросмотра карточку g1e039091 (Сбербанк продаёт
права требования к застройщику ЖК «Новый город» в Выборге) — та же новость,
тот же URL, что и удалённая часом ранее g784c5e92 (владелец: «продажа прав
требования это не сделка не делай карточку», см. KNOWN_ISSUES.md запись
23 сентября 2026). Ворота `promote.py` не знали об этом решении (память
`discarded_urls` пишет только `approve.py` при вердикте discard в консоли,
а до консоли эта карточка ещё не доехала) и пропустили черновик повторно.

Действие — то же самое, что кнопка «🗑 Выкинуть» в консоли: карточка
убирается из `pending.json`, а URL записывается в `discarded_urls`
(`moderation_state.json`), чтобы `promote.py` больше не пропускал этот же
адрес — тем же механизмом, что уже используется для ручных записей (Wildberries/
ВТБ, RTP Global/Ahead Health).

Запуск:
    python3 pipeline/discard_pending_card_2026_09_23.py            # сухой прогон
    python3 pipeline/discard_pending_card_2026_09_23.py --write    # применить
"""
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
STATE = os.path.join(ROOT, 'data', 'inbox', 'moderation_state.json')

CARD_ID = 'g1e039091'
URL = 'https://www.dp.ru/a/2026/09/23/sberbank-prodajot-prava-trebovanija'
TITLE_PART = 'Сбербанк продаёт права требования'


def main(write=False):
    data = json.load(open(PENDING, encoding='utf-8'))
    card = next((c for c in data['cards'] if c['id'] == CARD_ID), None)
    if not card:
        print('НЕ ТРОГАЕМ %s — карточки уже нет в очереди' % CARD_ID)
        return 0
    if TITLE_PART.lower() not in str(card.get('title') or '').lower():
        print('НЕ ТРОГАЕМ %s — заголовок не совпадает: %r' % (CARD_ID, card.get('title')))
        return 1
    if card.get('draft_sent') or card.get('post_draft_sent'):
        print('НЕ ТРОГАЕМ %s — карточка уже показана в консоли, тут решает человек' % CARD_ID)
        return 1
    print('ВЫКИДЫВАЕМ %s %s' % (CARD_ID, card['title']))
    print('           та же не-сделка, что владелец уже отклонил (g784c5e92)')
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
        'note': 'выкинута по прежнему решению владельца (не на консольную кнопку, а по заметке '
                'о карточке g784c5e92 с тем же URL) — продажа прав требования не сделка для базы',
    }
    json.dump(state, open(STATE, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено: карточка убрана, URL записан в discarded_urls.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
