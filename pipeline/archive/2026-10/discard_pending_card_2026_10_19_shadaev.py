# -*- coding: utf-8 -*-
"""Убрать из очереди предпросмотра карточку g3d4728f7 («Право встретиться
с Шадаевым продали на аукционе за 10,4 млн рублей») — ворота `promote.py`
пропустили ее как «ПУСТИТЬ» (единственный элемент, НА РЕШЕНИЕ ее не
остановило), хотя это не сделка: лот благотворительного аукциона Meet For
Charity (личная встреча с главой Минцифры), а не покупка компании или
актива. Признак, который ворота не поймали, — весь заголовок ушел в
`seller` («Право встретиться с Шадаевым»), а `buyer_name` пуст.

Действие — то же самое, что кнопка «🗑 Выкинуть» в консоли (см.
`docs/intake_run.md`, шаги 5–6): карточка убирается из `pending.json`, URL
идет в `discarded_urls`, черновик `d10080017` помечается
`decided_raw`/`raw_titles` как `auto-drop`, чтобы `promote.py` не завел ее
снова из старого сырья на следующем часе.

Запуск:
    python3 pipeline/discard_pending_card_2026_10_19_shadaev.py            # сухой прогон
    python3 pipeline/discard_pending_card_2026_10_19_shadaev.py --write    # применить
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

CARD_ID = 'g3d4728f7'
DRAFT_ID = 'd10080017'
URL = 'https://iz.ru/2186783/pravo-vstretitsia-s-shadaevym-prodali-na-auktcione-za-104-mln-rublei'
TITLE = 'Право встретиться с Шадаевым продали на аукционе за 10,4 млн рублей'


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
    print('           лот благотворительного аукциона (встреча с министром), не сделка')
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
        'note': 'лот благотворительного аукциона Meet For Charity (личная встреча с '
                'министром цифрового развития), не покупка компании или актива',
    }
    state.setdefault('decided_raw', {})[DRAFT_ID] = 'auto-drop'
    state.setdefault('raw_titles', {})[promote.raw_key(TITLE)] = 'auto-drop'
    json.dump(state, open(STATE, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено: карточка убрана, URL и черновик записаны в moderation_state.json.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
