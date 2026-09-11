# -*- coding: utf-8 -*-
"""Приток 11 сентября 2026 (11:20 МСК) — реальная сделка, которую ворота
не пропустили: разбор заголовка (пост в Telegram-канале «Русский Венчур»,
обрубленный на 260 знаках — тот же класс, что уже описан в CLAUDE.md для
`events[].note`, только здесь это исходное сырьё, а не наша карточка)
не смог выделить ни одной стороны и записал в `asset` хвост фразы вместо
имени компании.

Источники: WebSearch нашёл дословный пересказ поста на vc.ru (канал
«Русский Венчур» ведёт колонку там же) — статья цитирует исходный пост
целиком и добавляет собственные факты о покупателе и финансах цели,
которых не было в обрубленном Telegram-черновике.

Продавец — Сергей Жучков, основатель ProgKids (сама компания и есть
предмет сделки — `asset`, не «Rocket Tech School», как ошибочно распарсил
приток: Rocket Tech School — ПОКУПАТЕЛЬ). Сумма и условия сделки не
разглашаются — не выдумывается ни цифра, ни доля. Сделка стала экзитом
для фонда Impact Capital (Валерий Золотухин), вложившего $50 тыс. в
2021 году.

Запуск: python3 pipeline/fix_add_progkids_rocket_tech_school.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ROOT)
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
PENDING_PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')
STATE_PATH = os.path.join(ROOT, 'data', 'inbox', 'moderation_state.json')
BASE_PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

SRC_URL_VC = 'https://vc.ru/id4994551/3049740-prodazha-progkids-i-ekzit-dlya-impact-capital'
SRC_URL_TG = 'https://t.me/rusven/7634'
DRAFT_ID = 'd58253385'

TARGET_ID = 'gprogkids'
TARGET_NAME = 'ProgKids'
BUYER_ID = 'grocketts'
BUYER_NAME = 'Rocket Tech School'

QUOTE_MAIN = (
    'Основатель онлайн-школы программирования для детей и подростков '
    'ProgKids Сергей Жучков продал компанию Rocket Tech School.'
)

QUOTE_BUYER_DESC = (
    'Rocket Tech School - международная онлайн-школа программирования и '
    'цифрового творчества для детей от 5 до 17 лет... работает более чем '
    'в 50 странах. В школе учится свыше 3 тыс. учеников.'
)

QUOTE_RATIONALE = (
    'Сделка стала экзитом для фонда Impact Capital под управлением '
    'Валерия Золотухина, который в 2021 году вложил в проект $50 тысяч.'
)

QUOTE_TARGET_FIN = (
    'Выручка юрлица за 2025 год составила 56 млн рублей, чистый убыток - '
    '1,4 млн рублей.'
)


def main(write=False):
    import promote

    with open(PENDING_PATH, encoding='utf-8') as f:
        pending = json.load(f)
    with open(STATE_PATH, encoding='utf-8') as f:
        state = json.load(f)
    with open(BASE_PATH, encoding='utf-8') as f:
        base = json.load(f)

    existing_ids = {c['id'] for c in pending['cards']}
    assert not any('ProgKids' in (c.get('title') or '')
                   for c in pending['cards']), \
        'карточка про ProgKids уже есть в pending.json'
    assert TARGET_ID not in base['companies'], \
        'профиль %s уже есть' % TARGET_ID
    assert BUYER_ID not in base['companies'], \
        'профиль %s уже есть' % BUYER_ID

    new_id = promote.new_id(existing_ids)
    card = {
        'id': new_id,
        'date': '2026-07-27',
        'title': 'Сергей Жучков продал ProgKids компании Rocket Tech School',
        'ind': 'Образование',
        'type': 'M&A',
        'status': 'Закрыта',
        'src': [['vc.ru', SRC_URL_VC], ['Русский Венчур (Telegram)', SRC_URL_TG]],
        'from_ingest': True,
        'eco': {'sum': '—', 'share': '—', 'val': '—',
                'target_fin': QUOTE_TARGET_FIN,
                'fin': '—', 'rationale': QUOTE_RATIONALE, 'context': '—',
                'finadv': '—'},
        'law': {'struct': '—', 'appr': '—', 'adv': [], 'terms': '—'},
        'buyer': BUYER_ID,
        'seller': 'Сергей Жучков',
        'target': TARGET_ID,
        'events': [{
            'kind': 'closed',
            'date': '2026-07-27',
            'title': 'Сделка завершена',
            'note': QUOTE_MAIN + ' Условия и сумма сделки не разглашаются.',
            'source': ['vc.ru', SRC_URL_VC],
        }],
    }

    pending['cards'].append(card)
    state.setdefault('decided_raw', {})[DRAFT_ID] = 'take'

    base['companies'][TARGET_ID] = {
        'name': TARGET_NAME,
        'ind': 'Образование',
        'desc': ('Онлайн-школа программирования для детей и подростков: '
                 'учит программировать на базе Minecraft и Roblox.'),
        'kpi': ['Профиль', 'Автоматический'],
    }
    base['companies'][BUYER_ID] = {
        'name': BUYER_NAME,
        'ind': 'Образование',
        'desc': ('Международная онлайн-школа программирования и цифрового '
                 'творчества для детей 5-17 лет, работает в 50+ странах.'),
        'kpi': ['Профиль', 'Автоматический'],
    }
    base.setdefault('match_keys', {})[TARGET_ID] = ['progkids', 'прогкидс']
    base.setdefault('match_keys', {})[BUYER_ID] = ['rocket tech school']

    print('Добавлена карточка %s: ProgKids/Rocket Tech School.' % new_id)

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
