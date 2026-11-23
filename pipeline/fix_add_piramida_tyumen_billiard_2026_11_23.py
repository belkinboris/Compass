# -*- coding: utf-8 -*-
"""Карточка: помещение бильярдного клуба «Пирамида Тюмень» выставлено на
продажу за 40 млн рублей — анонимное объявление на площадке бесплатных
объявлений (тот же класс, что gb4937a72, завод скотча в Тюмени, 23 ноября
2026): продавец и покупатель не названы, честная пустота с обеих сторон.

ИСТОЧНИК: URA.RU, https://ura.news/news/1053146585

Запуск:
    python3 pipeline/fix_add_piramida_tyumen_billiard_2026_11_23.py            # сухой прогон
    python3 pipeline/fix_add_piramida_tyumen_billiard_2026_11_23.py --write    # запись
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
URA_URL = 'https://ura.news/news/1053146585'


def gid(key):
    return 'g' + hashlib.sha1(key.encode('utf-8')).hexdigest()[:8]


DEAL_ID = gid('piramida-tyumen-billiard-club-sale-2026-11-23')


def build_card():
    return {
        'id': DEAL_ID,
        'date': '2026-11-23',
        'title': 'Помещение бильярдного клуба «Пирамида Тюмень» выставлено на продажу за 40 млн рублей',
        'ind': 'Развлечения',
        'type': 'M&A',
        'status': 'Обсуждается',
        'src': [['URA.RU', URA_URL]],
        'from_ingest': True,
        'eco': {
            'sum': '40 млн ₽',
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
        'sum': '40 млн ₽',
        'asset': 'Помещение бильярдного клуба «Пирамида Тюмень»',
        'seller_src': 'text',
        'party_evidence': {
            'target': [{'value': 'Помещение бильярдного клуба «Пирамида Тюмень»', 'field': 'asset',
                        'method': 'explicit_news_title', 'url': URA_URL}],
        },
        'pending_since': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'from_raw': {'draft_id': 'd25514328', 'title': 'В Тюмени продают помещение популярного бильярдного клуба'},
        'accepted_notes': {
            'no_profile': {
                'seller': ('Продавец — автор объявления на площадке бесплатных объявлений; имя '
                           'человека и название юридического лица в источнике не называются — '
                           'честная пустота, профиль не заводим.'),
                'buyer': 'объявление о продаже — покупателя еще нет, профиль не заводим.',
                'target': ('Бильярдный клуб «Пирамида Тюмень» (ул. Холодильная) — анонимное '
                           'объявление, юрлицо-владелец не названо; профиль не заводим.'),
            },
            'searched': ('URA.RU, 23.11.2026 (первоисточник, прочитан целиком через '
                          'fetch_article_texts.py) — единственная найденная публикация об этом '
                          'объявлении.'),
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
