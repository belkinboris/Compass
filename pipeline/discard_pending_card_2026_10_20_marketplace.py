# -*- coding: utf-8 -*-
"""Убрать из очереди предпросмотра карточку ge4de7581 («Маркетплейсы
рассказали, что россияне чаще покупают из спорттоваров») — ворота
`promote.py` пропустили её как «ПУСТИТЬ», хотя это потребительская
статистика о покупках на маркетплейсах (РБК «Общество»), а не сделка.
Признак — бессмысленные поля черновика: весь заголовок бессвязно
поделён между `buyer_name` («Маркетплейсы рассказали, что россияне
чаще») и `asset` («из спорттоваров») — тот же класс ложного
срабатывания, что уже описан в `docs/intake_run.md`, шаги 5–6. Источник
(rbc.ru) при этом вернул пустой текст (0 знаков) — страница недоступна
обычным способом, но заголовок сам по себе уже достаточно ясен.

Действие — то же самое, что кнопка «🗑 Выкинуть»: карточка убирается из
`pending.json`, URL — в `discarded_urls`, черновик `d74758946` —
`decided_raw`/`raw_titles`, чтобы `promote.py` не завёл её снова.

Запуск:
    python3 pipeline/discard_pending_card_2026_10_20_marketplace.py            # сухой прогон
    python3 pipeline/discard_pending_card_2026_10_20_marketplace.py --write    # применить
"""
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import promote  # noqa: E402

PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
STATE = os.path.join(ROOT, 'data', 'inbox', 'moderation_state.json')

CARD_ID = 'ge4de7581'
DRAFT_ID = 'd74758946'
URL = 'https://www.rbc.ru/society/20/10/2026/6ad5e7fe9a7947c5ba91f1de'
TITLE = 'Маркетплейсы рассказали, что россияне чаще покупают из спорттоваров'


def main(write=False):
    data = json.load(open(PENDING, encoding='utf-8'))
    card = next((c for c in data['cards'] if c['id'] == CARD_ID), None)
    if not card:
        print('НЕ ТРОГАЕМ %s — карточки уже нет в очереди' % CARD_ID)
        return 0
    if card['title'] != TITLE:
        print('НЕ ТРОГАЕМ %s — заголовок не совпадает: %r' % (CARD_ID, card.get('title')))
        return 1
    if card.get('draft_sent') or card.get('post_draft_sent'):
        print('НЕ ТРОГАЕМ %s — карточка уже показана в консоли, тут решает человек' % CARD_ID)
        return 1
    print('ВЫКИДЫВАЕМ %s %s' % (CARD_ID, card['title']))
    print('           потребительская статистика маркетплейсов, не сделка')
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
        'note': 'потребительская статистика покупок на маркетплейсах (РБК «Общество»), '
                'не покупка компании или актива — заголовок бессвязно разобран на '
                'buyer_name/asset',
    }
    state.setdefault('decided_raw', {})[DRAFT_ID] = 'auto-drop'
    state.setdefault('raw_titles', {})[promote.raw_key(TITLE)] = 'auto-drop'
    json.dump(state, open(STATE, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено: карточка убрана, URL и черновик записаны в moderation_state.json.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
