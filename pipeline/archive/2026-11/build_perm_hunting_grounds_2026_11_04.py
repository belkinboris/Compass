# -*- coding: utf-8 -*-
"""Строит карточку из очереди сомнительного сырья, снятой raw_screen.py
4 ноября 2026 (приток, 10:20 МСК): частное объявление о продаже на
классифайдах, тот же класс, что g4e184429/g90784f0a/g17a522dc —
продавец и покупатель не раскрыты, профили не заводятся.

d65285216: охотничьи угодья «Волынское» (52 тыс. га, долгосрочная аренда
на 49 лет) в Красновишерском округе Пермского края, 4 млн рублей (URA.RU).

Запуск: python3 pipeline/archive/2026-11/build_perm_hunting_grounds_2026_11_04.py
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

draft = {
    'date': '2026-11-04',
    'title': 'В Пермском крае продают право долгосрочной аренды охотничьих угодий «Волынское» за 4 млн рублей',
    'ind': 'Недвижимость',
    'type': 'M&A',
    'status': 'Обсуждается',
    'src': [['web:ura.news', 'https://ura.news/news/1053141280']],
    'events': [],
    'sum': '4 млн ₽',
    'seller': None,
    'buyer_name': None,
    'asset': 'право долгосрочной аренды охотничьего хозяйства «Волынское» площадью 52 тыс. га в Красновишерском округе Пермского края',
}

deal_id = promote.new_id(existing)
card = promote.to_card(draft, deal_id)
card['pending_since'] = datetime.now(timezone.utc).isoformat()
pending['cards'].append(card)
print(deal_id, '->', card['title'])

with open(PENDING, 'w', encoding='utf-8') as f:
    json.dump(pending, f, ensure_ascii=False, indent=1)
    f.write('\n')
print('Записано:', PENDING)
