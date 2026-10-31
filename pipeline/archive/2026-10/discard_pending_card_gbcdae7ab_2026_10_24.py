# -*- coding: utf-8 -*-
"""Убрать из очереди предпросмотра карточку gbcdae7ab (Тевтонский замок
XIV века в Калининградской области купили за 734 тысячи рублей) — ворота
`promote.py` пропустили ее как M&A (оба поля формально заполнены), но
статья целиком прочитана и это не сделка для базы: руины замка Заалау
(поселок Каменское) продали на аукционе ДОМ.РФ, покупатель — «писатель и
исследователь», частное лицо, а не компания; масштаб (734 тыс. ₽) далек
от M&A. Заодно поля черновика были бессмысленными: buyer_name содержал
сам предмет («Тевтонский замок XIV века…»), а asset — цену («за 734
тысячи рублей») — тот же класс ложного срабатывания ворот, что уже
описан в docs/intake_run.md («личная покупка дома певицей» и т. п.).

Действие — то же самое, что кнопка «🗑 Выкинуть» в консоли: карточка
убирается из `pending.json`, URL — в `discarded_urls`, черновик —
`decided_raw`/`raw_titles` (как `raw_screen.py --drop`).

Запуск:
    python3 pipeline/discard_pending_card_gbcdae7ab_2026_10_24.py            # сухой прогон
    python3 pipeline/discard_pending_card_gbcdae7ab_2026_10_24.py --write    # применить
"""
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import promote  # noqa: E402

PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
STATE = os.path.join(ROOT, 'data', 'inbox', 'moderation_state.json')

CARD_ID = 'gbcdae7ab'
DRAFT_ID = 'd28119932'
URL = ('https://abnews.ru/szfo/news/kaliningrad/2026/10/24/'
       'tevtonskij-zamok-xiv-veka-v-kaliningradskoj-oblasti-kupili-za-734-tysyachi-rublej')
TITLE_PART = 'Тевтонский замок'


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
    print('           частная покупка руин замка физлицом на аукционе ДОМ.РФ, не M&A')
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
        'note': 'частное лицо (писатель) купило руины замка на аукционе ДОМ.РФ за 734 тыс. ₽ — '
                'не компания, не M&A для базы; поля черновика были перепутаны (buyer_name = предмет, '
                'asset = цена)',
    }
    state.setdefault('decided_raw', {})[DRAFT_ID] = 'auto-drop'
    state.setdefault('raw_titles', {})[promote.raw_key(card['title'])] = 'auto-drop'
    json.dump(state, open(STATE, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено: карточка убрана, URL и черновик записаны в память решений.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
