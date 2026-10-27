# -*- coding: utf-8 -*-
"""Убрать из очереди предпросмотра карточку g5c2c3086 («Бывший замдиректора
Депфина ЯНАО получил контроль над финансами Белгородской области») —
ворота `promote.py` пропустили ее как «ПУСТИТЬ», хотя это новость о
кадровом назначении на госдолжность (руководитель департамента финансов
региона), а не сделка. Признак — бессмысленные поля черновика: заголовок
бессвязно поделен между `buyer_name` («Бывший замдиректора Депфина ЯНАО»)
и `asset` («над финансами Белгородской области») — тот же класс ложного
срабатывания, что уже описан в `docs/intake_run.md`, шаги 5–6.

Действие — то же самое, что кнопка «🗑 Выкинуть»: карточка убирается из
`pending.json`, URL — в `discarded_urls`, черновик `d79584901` —
`decided_raw`/`raw_titles`, чтобы `promote.py` не завел ее снова.

Запуск:
    python3 pipeline/discard_pending_card_2026_10_20_belgorod_finance.py            # сухой прогон
    python3 pipeline/discard_pending_card_2026_10_20_belgorod_finance.py --write    # применить
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

CARD_ID = 'g5c2c3086'
DRAFT_ID = 'd79584901'
URL = 'https://ura.news/news/1053137482'
TITLE = 'Бывший замдиректора Депфина ЯНАО получил контроль над финансами Белгородской области'


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
    print('           кадровое назначение на госдолжность, не сделка')
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
        'note': 'кадровое назначение на госдолжность (руководитель финансов региона), '
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
