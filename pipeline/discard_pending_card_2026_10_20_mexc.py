# -*- coding: utf-8 -*-
"""Ворота пропустили не-сделку: «Криптобиржа MEXC ... объявила об уходе из
России» — по статье (Коммерсантъ, 20.10.2026) MEXC просто ПРЕКРАТИЛА
обслуживание клиентов из России и Белоруссии («в рамках постоянной работы
по совершенствованию системы соблюдения регуляторных требований») — нет ни
покупателя, ни продавца, ни передачи актива: средства клиентов остаются у
них же, площадка просто перестаёт работать с российскими пользователями
(тот же класс, что биржа Bitget неделей раньше). `seller` механически
заполнился всем заголовком целиком — классический признак ложного
срабатывания ворот (docs/intake_run.md, «Шаги 5-6: ворота пропустили
не-сделку»). Тема «Уход иностранного владельца» в базе всегда означает
продажу/передачу российского бизнеса конкретному покупателю (сверено по
деcяти карточкам с этой темой) — здесь продажи нет вовсе.

Действие — то же самое, что кнопка «🗑 Выкинуть» в консоли.

Запуск:
    python3 pipeline/discard_pending_card_2026_10_20_mexc.py            # сухой прогон
    python3 pipeline/discard_pending_card_2026_10_20_mexc.py --write    # применить
"""
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
STATE = os.path.join(ROOT, 'data', 'inbox', 'moderation_state.json')

CARD_ID = 'gc1aa22a6'
URL = 'https://www.kommersant.ru/doc/9043193'
TITLE_PART = 'Криптобиржа MEXC'


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
    print('           биржа просто прекратила обслуживание — нет ни покупателя, ни продавца, ни передачи актива')
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
        'note': 'MEXC просто прекратила обслуживание клиентов из РФ — нет сделки (ни покупателя, '
                'ни передачи актива), не продажа российского бизнеса',
    }
    json.dump(state, open(STATE, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
