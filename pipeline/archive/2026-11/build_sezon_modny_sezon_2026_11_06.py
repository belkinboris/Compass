# -*- coding: utf-8 -*-
"""Строит отдельную карточку о перепродаже галереи «Модный сезон».

КОНТЕКСТ. В базе есть карточка g67feb893 (2024, «Закрыта») — отель Four
Seasons и галерея «Модный сезон» обращены в доход государства по суду у
Алексея Хотина. 5-6 ноября 2026 Ведомости написали, что ЧАСТЬ того же
имущества (сама галерея, 41 000 кв. м) ПЕРЕПРОДАНА государством частному
покупателю — АО «Сезон», связанному со Сбербанком. Решение по
DUPLICATE_RESOLUTION_BRIEF.md: `separate` — другой тип сделки (продажа
Росимуществом, а не национализация по суду), другие стороны (покупатель —
АО «Сезон», а не государство), другой предмет сделки (продажа, а не
изъятие), 2+ года после национализации. Прецедент в самой базе — «Рольф»:
g77aa1026 (национализация, 2024-02-21) и g69a22dab (продажа структуре
Кремлева, 2024-08-31) — те же две карточки на одно и то же здание/бизнес.

Источник: Ведомости, https://www.vedomosti.ru/realty/articles/2026/11/05/
1242692-u-torgovoi-galerei-smenilsya-vladelets (платный материал, открыта
примерно треть — текст открытой части на диске, data/inbox/triage/
sources_2026-11-06.json, save_source.py). Второй источник с теми же
фактами — Retailer.ru (https://retailer.ru/galereja-modnyj-sezon-pereshla-
strukture-sberbanka/) — сеть отказала (DNS), прочитан только через
WebSearch-пересказ; независимой новой цитаты из него не беру, в `src` он
идёт вторым упоминанием. Коммерсантъ, РБК, Интерфакс, Mail.ru — искал,
нашёл только более старые материалы о самой национализации (ноябрь 2024)
и о продаже апартаментов ВТБ (март 2026, другая часть того же здания) —
ни тот, ни другой не об этой сделке. Сумма сделки ни в одном источнике не
названа — честная пустота, `sum` не ставится.

ИНН АО «Сезон» не нашёлся: ЕГРЮЛ (egrul.nalog.ru, 503), rusprofile (403),
checko (403), list-org (без совпадения по имени "АО Сезон" с учредителем
СБК ББ), audit-it (404); несколько запросов WebSearch с именем компании,
учредителем и датой регистрации результата не дали — `no_inn` при приёмке.

Запуск: python3 pipeline/archive/2026-11/build_sezon_modny_sezon_2026_11_06.py
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

import promote        # noqa: E402
import link_parties    # noqa: E402

PENDING = 'static/data/pending.json'
DATA = 'static/data/deals_promoted.json'

base = json.load(open(DATA, encoding='utf-8'))
pending = json.load(open(PENDING, encoding='utf-8'))
existing = {d['id'] for d in base['deals']} | {c['id'] for c in pending['cards']}

VEDOMOSTI_URL = ('https://www.vedomosti.ru/realty/articles/2026/11/05/'
                  '1242692-u-torgovoi-galerei-smenilsya-vladelets')

draft = {
    'date': '2026-10-30',
    'title': 'АО «Сезон» купило у Росимущества галерею «Модный сезон» у Кремля',
    'ind': 'Недвижимость',
    'type': 'M&A',
    'status': 'Закрыта',
    'src': [
        ['Ведомости', VEDOMOSTI_URL],
        ['Retailer.ru', 'https://retailer.ru/galereja-modnyj-sezon-pereshla-strukture-sberbanka/'],
    ],
    'seller': 'Росимущество',
    'buyer_name': 'АО «Сезон»',
    'asset': 'торговая галерея «Модный сезон» (41 000 кв. м) в здании отеля Four Seasons у Кремля',
}

# Карточка-предшественник (национализация, 2024) НЕ дубль — это другая сделка
# на том же активе два года спустя, см. docstring. Ставим метку по тому же
# правилу, что и resolve_duplicates.py для вердикта `separate`.
PREDECESSOR_ID = 'g67feb893'
predecessor = next((d for d in base['deals'] if d['id'] == PREDECESSOR_ID), None)
if predecessor is not None and not predecessor.get('separate_transaction_reviewed'):
    predecessor['separate_transaction_reviewed'] = True
    print('%s: separate_transaction_reviewed = true (национализация 2024 и '
          'перепродажа 2026 — разные сделки)' % PREDECESSOR_ID)

deal_id = promote.new_id(existing)
card = promote.to_card(draft, deal_id)

party_index = link_parties.build_index(base['companies'])
for line in link_parties.link_card(card, party_index, base['companies']):
    print('    %s | связано -> %s' % (deal_id, line))

card['pending_since'] = datetime.now(timezone.utc).isoformat(timespec='seconds')
pending['cards'].append(card)
print(deal_id, '->', card['title'])
print('themes:', card.get('themes'))
print('seller_id:', card.get('seller_id'), '| buyer:', card.get('buyer'), '| buyer_name:', card.get('buyer_name'))

with open(DATA, 'w', encoding='utf-8') as f:
    json.dump(base, f, ensure_ascii=False, indent=1)
    f.write('\n')
with open(PENDING, 'w', encoding='utf-8') as f:
    json.dump(pending, f, ensure_ascii=False, indent=1)
    f.write('\n')
print('Записано:', DATA, 'и', PENDING)
