# -*- coding: utf-8 -*-
"""Новая карточка по held-черновику d31799306 (приток, 24 ноября 2026):
механические ворота (`promote.py`) держали его, потому что заголовок
«Экс-владелец МИЦ Рябинский продал девелоперский проект в Московском
регионе» не называет ни одной стороны по форме — обе стороны названы
только в теле статьи.

ЧТО НАШЛОСЬ ПРИ ЧТЕНИИ ПОЛНОЙ СТАТЬИ (Ведомости, кэш на диске, 28% —
видимая часть под paywall, остальное для карточки не нужно). Покупатель —
ООО «Специализированный застройщик «Говорово парк»», принадлежащее
Николаю Никифорову, владельцу тюменского застройщика «Скандиа». Он выкупил
100% долей ООО «Специализированный застройщик «Бачурино»» — на балансе
компании участок 10 га в деревне Бачурино рядом с Коммунаркой в новой
Москве (данные сервиса Asseto). Сделка закрыта 1 октября 2026 года, по
данным «СПАРК-Интерфакса»; первым о ней написал Telegram-канал «Стройки –
и точка». Продавцом, по словам двух консультантов, знакомых с участниками
сделки, выступил бывший совладелец МИЦ Андрей Рябинский — сам он и
«Скандиа» на запросы издания не ответили; эта атрибуция НЕ подтверждена
первыми лицами, и формулировка карточки (`eco.context`, `law.struct`)
хедж сохраняет, а не превращает его в голый факт.

ИНН НАЙДЕНЫ (list-org.com, 24 ноября 2026, см. `accepted_notes.searched`
карточки): покупатель — 9705140589, цель — 9705131440. У обоих профилей в
list-org один директор — Никифоров Николай Юрьевич, и это само по себе
второе, механическое подтверждение связи с Никифоровым (а не только слова
статьи): директор цели сменился на него же, хотя до марта 2026 года
компанией управлял Рябинский (ЕГРЮЛ по тексту статьи).

ИСТОЧНИК: Ведомости, https://www.vedomosti.ru/realty/articles/2026/11/24/1414554-eks-vladelets-mits-prodal-proekt

Запуск:
    python3 pipeline/fix_add_bachurino_govorovo_park_2026_11_24.py            # сухой прогон
    python3 pipeline/fix_add_bachurino_govorovo_park_2026_11_24.py --write    # запись

После записи структурных полей — партия прозы (`eco.context`, `law.struct`)
в `pipeline/ingest/fixes/written_2026_11_24_bachurino_govorovo_park.py` и
`python3 pipeline/ingest/review.py --write`.
"""
import json
import os
import random
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'ingest'))

DATA = os.path.join(ROOT, '..', 'static', 'data', 'deals_promoted.json')
PENDING = os.path.join(ROOT, '..', 'static', 'data', 'pending.json')
ARTICLE_URL = ('https://www.vedomosti.ru/realty/articles/2026/11/24/'
               '1414554-eks-vladelets-mits-prodal-proekt')


def new_id(existing):
    """id того же вида g + 8 hex-знаков, как у остальных карточек и профилей."""
    while True:
        candidate = 'g%08x' % random.getrandbits(32)
        if candidate not in existing:
            return candidate


def build_companies(all_ids):
    buyer_id = new_id(all_ids)
    all_ids.add(buyer_id)
    target_id = new_id(all_ids)
    all_ids.add(target_id)

    buyer = {
        'name': 'Специализированный застройщик «Говорово парк»',
        'ind': 'Недвижимость',
        'desc': ('Специализированный застройщик — юридическое лицо девелоперского проекта '
                 '«Говорово парк» в новой Москве. Принадлежит Николаю Никифорову, владельцу '
                 'тюменского застройщика «Скандиа».'),
        'kpi': [],
        'inn': '9705140589',
        'legal_short': 'ООО «Специализированный застройщик «Говорово парк»»',
        'ownership': [{'name': 'Николай Никифоров', 'id': None, 'as_of': '2026-11',
                       'source': ['Ведомости', ARTICLE_URL]}],
    }
    target = {
        'name': 'Специализированный застройщик «Бачурино»',
        'ind': 'Недвижимость',
        'desc': ('Специализированный застройщик: на балансе компании участок 10 га в деревне '
                 'Бачурино рядом с Коммунаркой в новой Москве (данные сервиса Asseto). До марта '
                 '2026 года контролировался бывшим совладельцем МИЦ Андреем Рябинским, затем '
                 'перешел в его личный фонд «Сигма 66»; конечный бенефициар фонда не раскрывается.'),
        'kpi': [],
        'inn': '9705131440',
        'legal_short': 'ООО «Специализированный застройщик «Бачурино»»',
    }
    return buyer_id, buyer, target_id, target


def build_card(deal_id, buyer_id, target_id):
    return {
        'id': deal_id,
        'date': '2026-10-01',
        'date_basis': 'registry',
        'title': '«Говорово парк» купил 100% «Бачурино» у Андрея Рябинского',
        'ind': 'Недвижимость',
        'type': 'M&A',
        'kind': 'acquisition',
        'status': 'Закрыта',
        'stake_acquired': 100.0,
        'src': [['Ведомости', ARTICLE_URL]],
        'from_ingest': True,
        'from_raw': 'd31799306',
        # test_every_pending_card_has_pending_since: отметка, от которой
        # approve.py считает сутки молчания — карточка, заведенная мимо
        # promote.py, иначе остается без нее.
        'pending_since': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'sum': 'Не раскрыта',
        'buyer': buyer_id,
        'target': target_id,
        'asset': '«Бачурино»',
        'seller': 'Андрей Рябинский',
        'seller_src': 'text',
        'eco': {'sum': 'Не раскрыта', 'share': '—', 'val': '—', 'target_fin': '—', 'fin': '—',
                'rationale': '—', 'context': '—', 'finadv': '—'},
        'law': {'struct': '—', 'appr': '—', 'adv': [], 'terms': '—'},
        'party_evidence': {
            'buyer': [{'value': 'Специализированный застройщик «Говорово парк»', 'field': 'buyer',
                       'method': 'manual_source_review', 'url': ARTICLE_URL}],
            'target': [{'value': 'Специализированный застройщик «Бачурино»', 'field': 'target',
                        'method': 'manual_source_review', 'url': ARTICLE_URL}],
            'seller': [{'value': 'Андрей Рябинский', 'field': 'seller',
                        'method': 'manual_source_review', 'url': ARTICLE_URL}],
        },
        'accepted_notes': {
            'notes': ('Механические ворота (`promote.py`) держали черновик d31799306: заголовок '
                      'издания не называет ни одной стороны по форме — обе стороны и ИНН нашлись '
                      'только в теле статьи и в реестрах. Продавец назван по словам двух '
                      'консультантов, знакомых с участниками сделки, — это не подтверждено ни '
                      'Рябинским (с ним не связались), ни «Скандиа» (не ответили на запрос); '
                      'модальность сохранена в `eco.context`/`law.struct`, а не снята.'),
            'searched': ('Ведомости, 24.11.2026 (первоисточник, прочитан целиком через '
                         'fetch_article_texts.py — факты лежат в открытых 28% текста). ИНН искал '
                         'по двум сторонам минимум в пяти источниках: WebSearch (несколько '
                         'запросов, включая site:list-org.com, site:datanewton.ru) не нашел прямых '
                         'карточек; rusprofile.ru и zachestnyibiznes.ru отдали 403 (защита от '
                         'ботов); checko.ru — 403; egrul.org (через egrul.itsoft.ru) — контент по '
                         'подписке, недоступен; list-org.com отдал обе карточки по текстовому '
                         'поиску («Говорово парк», «Бачурино») с ИНН/КПП/адресом/директором. '
                         'Директор обоих юрлиц в list-org — Никифоров Николай Юрьевич, что '
                         'независимо (механически, не только по словам статьи) подтверждает связь '
                         'покупателя с Никифоровым, а смена директора у цели на него же — что '
                         'сделка отражена в текущих данных реестра. Андрей Рябинский и Александр '
                         'Копылков — физические лица, профиль не заводится.'),
        },
    }


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    pending = json.load(open(PENDING, encoding='utf-8')) if os.path.exists(PENDING) else {'cards': []}

    assert not any('Бачурино' in (c.get('name') or '') or 'Говорово парк' in (c.get('name') or '')
                   for c in data['companies'].values()), 'профиль уже есть — скрипт не для повтора'

    all_ids = set(data['companies']) | {d['id'] for d in data['deals']} | {c['id'] for c in pending['cards']}
    buyer_id, buyer, target_id, target = build_companies(all_ids)
    deal_id = new_id(all_ids)

    card = build_card(deal_id, buyer_id, target_id)

    print('Новые профили:')
    print('  buyer  %s  %s  ИНН %s' % (buyer_id, buyer['name'], buyer['inn']))
    print('  target %s  %s  ИНН %s' % (target_id, target['name'], target['inn']))
    print('Новая карточка: %s' % deal_id)
    print('  title: %s' % card['title'])

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    data = json.load(open(DATA, encoding='utf-8'))
    assert buyer_id not in data['companies'] and target_id not in data['companies'], \
        'коллизия id при повторном чтении — перезапустите скрипт'
    data['companies'][buyer_id] = buyer
    data['companies'][target_id] = target
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

    pending = json.load(open(PENDING, encoding='utf-8')) if os.path.exists(PENDING) else {'cards': []}
    assert not any(c['id'] == deal_id for c in pending['cards']), 'карточка уже есть в pending.json'
    pending['cards'].append(card)
    json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

    print('\nЗАПИСАНО: 2 профиля в deals_promoted.json, 1 карточка в pending.json (id %s).' % deal_id)
    print('Теперь: python3 pipeline/ingest/raw_screen.py --drop d31799306 --reason "..." --write')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
