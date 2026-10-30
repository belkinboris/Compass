# -*- coding: utf-8 -*-
"""Разбор черновика d55306904 (база отдыха «Иртышская Ривьера», Омская
область) вручную — тот же обход ворот promote.py, что делает
`resolve_duplicates._promote_as_separate()`.

ПОЧЕМУ ВРУЧНУЮ. Механический разбор заголовка («Базу отдыха «Иртышская
ривьера» в элитном селе Омска вновь продают и подняли цену») не нашёл ни
стороны, ни предмета — из заголовка и правда не видно, кто продаёт. Но
источник (abnews.ru, 28 октября 2026) называет продавца прямо: ООО «Иртыш
Ривьера», принадлежащее Сергею Милютину. Это не анонимное объявление о
недвижимости без стороны — продавец назван, актив описан, есть финансы
компании и история цены. Карточка собирается чтением, разово.

Продавец и предмет оставлены пустыми здесь и дописаны `review.py` с
дословной цитатой (FIXES), чтобы `party_evidence` указывал на настоящий
метод (`human_review`) и адрес источника, а не на автоматическую, но
неверную пометку `explicit_news_title` (сторона не названа в заголовке).

Запуск: python3 pipeline/build_d55306904_irtysh_riviera_2026_10_30.py
"""
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
INGEST = os.path.join(ROOT, 'pipeline', 'ingest')
sys.path.insert(0, INGEST)

import promote           # noqa: E402
import link_parties      # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DRAFT = {
    'draft_id': 'd55306904',
    'date': '2026-10-28',
    # Заголовок — своя конструкция (CLAUDE.md, card_parties.md), не
    # перестановка слов исходного «Базу отдыха «Иртышская ривьера» в
    # элитном селе Омска вновь продают и подняли цену».
    'title': '«Иртыш Ривьера» повторно продаёт базу отдыха «Иртышская Ривьера» под Омском',
    'src': [['web:abnews.ru',
             'https://abnews.ru/siberia/news/omsk/2026/10/28/'
             'bazu-otdyha-v-elitnom-sele-omska-vnov-prodayut-i-podnyali-czenu']],
    # Выставленная цена — не цена сделки (покупателя нет); card_money.md:
    # «оценка... при выставлении на продажу» идёт в eco.val, а не в sum.
    'sum': None,
    'type': 'M&A',
    'status': 'Обсуждается',
    'ind': 'Гостиницы и туризм',
    'buyer_name': None,
    # seller/asset дописываются review.py с цитатой — см. docstring выше.
    'seller': None,
    'asset': None,
    'events': [],
}


def main():
    data = json.load(open(DATA, encoding='utf-8'))
    pending = promote.load_pending()
    existing = {d['id'] for d in data['deals']} | {c['id'] for c in pending['cards']}
    deal_id = promote.new_id(existing)
    card = promote.to_card(DRAFT, deal_id)
    party_index = link_parties.build_index(data['companies'])
    for line in link_parties.link_card(card, party_index, data['companies']):
        print('  %s | связано -> %s' % (deal_id, line))
    card['pending_since'] = datetime.now(timezone.utc).isoformat(timespec='seconds')
    pending['cards'].append(card)
    promote.save_pending(pending)
    print('СОЗДАНО: %s (бывший черновик d55306904)' % deal_id)
    return deal_id


if __name__ == '__main__':
    main()
