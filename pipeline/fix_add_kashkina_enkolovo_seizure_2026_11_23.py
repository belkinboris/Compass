# -*- coding: utf-8 -*-
"""Новая карточка: активы экс-замглавы УФНС по Ленобласти Светланы Кашкиной
(два участка, дом и гараж в деревне Энколово) обращены в доход государства —
решение Приморского районного суда Петербурга, 23 ноября 2026.

ЗАЧЕМ. Черновик придержан воротами («не установлен предмет сделки» — из
заголовка не видно, что изымают). По смыслу это тот же класс карточек,
что уже есть в базе («Изъятие», g025fc7ae «КИ Инвест»): суд решил, кто
продавца и покупателя нет, деньги не платились, актив перешел государству
по решению суда за несоответствие доходам.

ИСТОЧНИК: Фонтанка, https://www.fontanka.ru/2026/11/23/76785282/

Запуск:
    python3 pipeline/fix_add_kashkina_enkolovo_seizure_2026_11_23.py            # сухой прогон
    python3 pipeline/fix_add_kashkina_enkolovo_seizure_2026_11_23.py --write    # запись
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
FONTANKA_URL = 'https://www.fontanka.ru/2026/11/23/76785282/'


def gid(key):
    return 'g' + hashlib.sha1(key.encode('utf-8')).hexdigest()[:8]


DEAL_ID = gid('kashkina-enkolovo-seizure-2026-11-23')


def build_card():
    return {
        'id': DEAL_ID,
        'date': '2026-11-23',
        'title': 'Активы экс-замглавы УФНС по Ленобласти Светланы Кашкиной обращены в доход государства',
        'ind': 'Недвижимость',
        'type': 'M&A',
        'status': 'Закрыта',
        'src': [['Фонтанка', FONTANKA_URL]],
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
            'terms': 'Деньги за актив не платились: изъят без компенсации, по решению суда за '
                     'несоответствие расходов доходам.',
        },
        'asset': 'Участки, дом и гараж в Энколово',
        'no_parties': 'Изъятие по решению суда: покупателя и продавца нет, активы перешли государству.',
        'party_evidence': {
            'target': [{'value': 'Участки, дом и гараж в Энколово', 'field': 'asset',
                        'method': 'explicit_news_title', 'url': FONTANKA_URL}],
        },
        'pending_since': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'from_raw': {'draft_id': 'd68127159',
                     'title': 'Суд в Петербурге изъял в пользу государства дом и участки у '
                              'экс-замглавы налоговой службы Ленобласти'},
        'accepted_notes': {
            'no_profile': {
                'target': 'Предмет — земельные участки, жилой дом и гараж (недвижимое имущество '
                          'физического лица), а не юридическое лицо; профиль не заводим.',
            },
            'searched': ('Фонтанка, 23.11.2026 (первоисточник, прочитан целиком через '
                          'fetch_article_texts.py) — пересказывает решение Приморского районного '
                          'суда Петербурга и ссылается на собственный более ранний материал '
                          '(ноябрь 2024) о приговоре Кашкиной.'),
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
