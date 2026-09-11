# -*- coding: utf-8 -*-
"""Приток 11 сентября 2026 (16:20 МСК) — реальная сделка, которую ворота не
пропустили: заголовок называет предмет описательно («разработчик ПО для
финсектора»), а настоящее имя компании (ООО «Точный код») стоит только в
теле статьи.

Источник прочитан целиком (WebFetch, frankmedia.ru/304517): Райффайзенбанк
приобрёл 49% новой компании «Точный код» (зарегистрирована 9 сентября
2026 года); остальные 51% распределены между пятью физлицами-соучредителями
(Наталья Меньшикова — 18%, Эльвира Емец, Андрей Кабанов, Андрей Почеснев и
Шухрат Собиров — по 8,25% каждому). Сумма сделки не раскрыта. Тип —
«Инвестиция»: компания только что зарегистрирована, банк входит в капитал
СП с частными соучредителями (cash-in), а не покупает долю у продавца.

Запуск: python3 pipeline/fix_raiffeisen_tochny_kod.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
PENDING_PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')
STATE_PATH = os.path.join(ROOT, 'data', 'inbox', 'moderation_state.json')
BASE_PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

SRC_URL = 'https://frankmedia.ru/304517'
DRAFT_ID = 'd63043446'
BUYER_ID = 'g39cb6128'
TARGET_ID = 'gtochnykod'

QUOTE_MAIN = ('Райффайзенбанк вошел в капитал новой компании «Точный код» '
              'с долей 49%.')
QUOTE_STRUCT = ('Компания зарегистрирована 9 сентября 2026 года. Остальные '
                 '51% распределены между пятью физлицами-соучредителями: '
                 'Наталья Меньшикова — 18%, Эльвира Емец, Андрей Кабанов, '
                 'Андрей Почеснев и Шухрат Собиров — по 8,25% каждому. '
                 'Сумма сделки не раскрывается.')


def main(write=False):
    import promote

    with open(PENDING_PATH, encoding='utf-8') as f:
        pending = json.load(f)
    with open(STATE_PATH, encoding='utf-8') as f:
        state = json.load(f)
    with open(BASE_PATH, encoding='utf-8') as f:
        base = json.load(f)

    existing_ids = {c['id'] for c in pending['cards']}
    assert not any('Точный код' in (c.get('title') or '')
                   for c in pending['cards']), \
        'карточка про "Точный код" уже есть в pending.json'
    assert TARGET_ID not in base['companies'], 'профиль %s уже есть' % TARGET_ID

    new_id = promote.new_id(existing_ids)
    card = {
        'id': new_id,
        'date': '2026-09-09',
        'title': 'Райффайзенбанк вошёл в капитал разработчика ПО «Точный код»',
        'ind': 'ИТ и интернет',
        'type': 'Инвестиция',
        'status': 'Закрыта',
        'src': [['Frank Media', SRC_URL]],
        'from_ingest': True,
        'eco': {'sum': '—', 'share': '49%', 'val': '—',
                'target_fin': '—', 'fin': '—', 'rationale': '—',
                'context': QUOTE_STRUCT, 'finadv': '—'},
        'law': {'struct': '—', 'appr': '—', 'adv': [], 'terms': '—'},
        'buyer': BUYER_ID,
        'target': TARGET_ID,
        'events': [{
            'kind': 'closed',
            'date': '2026-09-09',
            'title': 'Сделка завершена',
            'note': QUOTE_MAIN + ' ' + QUOTE_STRUCT,
            'source': ['Frank Media', SRC_URL],
        }],
    }

    pending['cards'].append(card)
    state.setdefault('decided_raw', {})[DRAFT_ID] = 'take'

    base['companies'][TARGET_ID] = {
        'name': '«Точный код»',
        'ind': 'ИТ и интернет',
        'desc': 'Разработчик программного обеспечения для финансового сектора.',
        'kpi': ['Профиль', 'Автоматический'],
    }
    base.setdefault('match_keys', {})[TARGET_ID] = ['точный код']

    print('Добавлена карточка %s: Райффайзенбанк/«Точный код».' % new_id)

    if write:
        with open(PENDING_PATH, 'w', encoding='utf-8') as f:
            json.dump(pending, f, ensure_ascii=False, indent=1)
            f.write('\n')
        with open(STATE_PATH, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=1)
            f.write('\n')
        with open(BASE_PATH, 'w', encoding='utf-8') as f:
            json.dump(base, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Записано.')
    else:
        print('(сухой прогон, для записи — --write)')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
