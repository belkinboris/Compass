# -*- coding: utf-8 -*-
"""Ворота пропустили не-сделку: «Анита Цой купила себе и мужу места на
кладбище» — личная покупка артистки, не рыночная сделка для базы (тот же
класс ложного срабатывания, что «личная покупка дома певицей», docs/
intake_run.md, «Шаги 5-6: ворота пропустили не-сделку»). `buyer_name`
механически заполнился именем артистки, `asset` — обрывком заголовка.

Действие — то же самое, что кнопка «🗑 Выкинуть» в консоли: карточка
убирается из `pending.json`, URL записывается в `discarded_urls`, чтобы
`promote.py` не пропустил его снова.

Запуск:
    python3 pipeline/discard_pending_card_2026_10_20_anita_tsoi.py            # сухой прогон
    python3 pipeline/discard_pending_card_2026_10_20_anita_tsoi.py --write    # применить
"""
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
STATE = os.path.join(ROOT, 'data', 'inbox', 'moderation_state.json')

CARD_ID = 'g9a8bbd5c'
URL = 'https://ura.news/news/1053137680'
TITLE_PART = 'Анита Цой купила себе и мужу места на кладбище'


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
    print('           личная покупка артистки — не рыночная сделка')
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
        'note': 'личная покупка мест на кладбище артисткой — не рыночная M&A-сделка',
    }
    json.dump(state, open(STATE, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
