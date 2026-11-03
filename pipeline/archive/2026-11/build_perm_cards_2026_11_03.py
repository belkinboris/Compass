# -*- coding: utf-8 -*-
"""Строит две новые карточки из очереди сомнительного сырья, снятой
raw_screen.py 3 ноября 2026 (приток, 18:20 МСК): частные объявления о
продаже на классифайдах, тот же класс, что g17a522dc/g861c5553 —
продавец и покупатель не раскрыты, профили не заводятся.

d35681708: деловой центр «Волна» в Перми, 400 млн ₽ (URA.RU).
d61105597: детский лагерь у санатория «Усть-Качка» в Пермском крае,
90 млн ₽ (URA.RU).

Запуск: python3 pipeline/archive/2026-11/build_perm_cards_2026_11_03.py
"""
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import promote  # noqa: E402

PENDING = 'static/data/pending.json'
DATA = 'static/data/deals_promoted.json'

base = json.load(open(DATA, encoding='utf-8'))
pending = json.load(open(PENDING, encoding='utf-8'))
existing = {d['id'] for d in base['deals']} | {c['id'] for c in pending['cards']}

drafts = [
    {
        'date': '2026-11-03',
        'title': 'В Перми продают здание делового центра «Волна» за 400 млн рублей',
        'ind': 'Недвижимость',
        'type': 'M&A',
        'status': 'Обсуждается',
        'src': [['web:ura.news', 'https://ura.news/news/1053141325']],
        'events': [],
        'sum': '400 млн ₽',
        'seller': None,
        'buyer_name': None,
        'asset': 'отдельно стоящее пятиэтажное здание делового центра «Волна» с земельным участком в собственности',
    },
    {
        'date': '2026-11-03',
        'title': 'В Пермском крае продают детский лагерь у санатория «Усть-Качка» за 90 млн рублей',
        'ind': 'Недвижимость',
        'type': 'M&A',
        'status': 'Обсуждается',
        'src': [['web:ura.news', 'https://ura.news/news/1053141355']],
        'events': [],
        'sum': '90 млн ₽',
        'seller': None,
        'buyer_name': None,
        'asset': 'действующий детский лагерь в районе Усть-Качки',
    },
]

for draft in drafts:
    deal_id = promote.new_id(existing)
    existing.add(deal_id)
    card = promote.to_card(draft, deal_id)
    card['pending_since'] = datetime.now(timezone.utc).isoformat()
    pending['cards'].append(card)
    print(deal_id, '->', card['title'])

with open(PENDING, 'w', encoding='utf-8') as f:
    json.dump(pending, f, ensure_ascii=False, indent=1)
    f.write('\n')
print('Записано:', PENDING)
