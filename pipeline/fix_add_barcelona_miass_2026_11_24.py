# -*- coding: utf-8 -*-
"""Новая карточка: спортивная база «Барселона» в Миассе (Челябинская обл.)
выставлена на продажу за 185 млн рублей — анонимное объявление на Авито
(тот же класс, что gb4937a72/g9550db70/g70cf2d0f/g6e759772/g221460e5,
собранные этой сессией 23-24 ноября 2026): продавец и покупатель не
названы, честная пустота с обеих сторон.

ИСТОЧНИК: URA.RU, https://ura.news/news/1053146930

Запуск:
    python3 pipeline/fix_add_barcelona_miass_2026_11_24.py            # сухой прогон
    python3 pipeline/fix_add_barcelona_miass_2026_11_24.py --write    # запись
"""
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'ingest'))

PENDING = os.path.join(ROOT, '..', 'static', 'data', 'pending.json')
URA_URL = 'https://ura.news/news/1053146930'
DRAFT_ID = 'd64459989'


def gid(key):
    return 'g' + hashlib.sha1(key.encode('utf-8')).hexdigest()[:8]


DEAL_ID = gid('barcelona-sport-base-miass-2026-11-24')


def build_card():
    return {
        'id': DEAL_ID,
        'date': '2026-11-24',
        'title': 'Спортивная база «Барселона» в Миассе выставлена на продажу за 185 млн рублей',
        'ind': 'Гостиницы и туризм',
        'type': 'M&A',
        'status': 'Обсуждается',
        'src': [['URA.RU', URA_URL]],
        'from_ingest': True,
        'eco': {
            'sum': '—',
            'share': '—',
            'val': '—',
            'target_fin': '—',
            'fin': '—',
            'rationale': '—',
            'context': '—',
            'finadv': '—',
        },
        'law': {
            'struct': '—',
            'appr': '—',
            'adv': [],
            'terms': '—',
        },
        'sum': '185 млн ₽',
        'asset': 'Спортивная база «Барселона» на берегу Поликарпова пруда в Миассе',
        'seller_src': 'text',
        'party_evidence': {
            'target': [{'value': 'Спортивная база «Барселона» на берегу Поликарпова пруда в Миассе',
                        'field': 'asset', 'method': 'explicit_news_title', 'url': URA_URL}],
        },
        'pending_since': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'from_raw': {'draft_id': DRAFT_ID,
                     'title': 'На челябинском курорте продается спортбаза «Барселона» за 185 миллионов рублей. Скрин'},
        'accepted_notes': {
            'no_profile': {
                'seller': ('Продавец — автор объявления на площадке «Авито»; имя человека и название '
                           'юридического лица в источнике не называются — честная пустота, профиль не заводим.'),
                'buyer': 'объявление о продаже — покупателя еще нет, профиль не заводим.',
                'target': ('Спортивная база «Барселона» в Миассе — анонимное объявление, юрлицо-владелец '
                           'не названо; профиль не заводим.'),
            },
            'searched': ('URA.RU, 24.11.2026 (первоисточник, прочитан целиком через '
                          'fetch_article_texts.py) — единственная найденная публикация об этом объявлении.'),
        },
    }


def main(write):
    pending = json.load(open(PENDING, encoding='utf-8'))
    assert DEAL_ID not in {c['id'] for c in pending['cards']}, 'карточка уже есть в pending.json'

    card = build_card()
    import tag_themes
    themes = tag_themes.add_themes(card)
    print('Карточка: %s' % card['id'])
    print('  title: %s' % card['title'])
    print('  themes: %s' % themes)

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    pending = json.load(open(PENDING, encoding='utf-8'))
    assert DEAL_ID not in {c['id'] for c in pending['cards']}
    pending['cards'].append(card)
    json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО: 1 карточка в pending.json')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
