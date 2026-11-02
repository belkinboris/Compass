# -*- coding: utf-8 -*-
"""Новая карточка: «Дом.РФ» выставил на торги право на КРТ в Воронеже.
Источник — РИА Недвижимость, 02.11.2026 (сохранен save_source.py). Черновик
d77717896 был ошибочно авто-выкинут raw_screen.py, потому что фетч в этот
момент принес пустое тело статьи (summary: "") — see known_issues/intake.md.
Карточка собирается вручную тем же путем, что promote.to_card().
Запуск: python3 build_voronezh_card.py --write (из pipeline/archive/2026-11)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
INGEST = '/home/user/Compass/pipeline/ingest'
sys.path.insert(0, INGEST)
import promote  # noqa: E402

ROOT = '/home/user/Compass'
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
STATE = os.path.join(ROOT, 'data', 'inbox', 'moderation_state.json')


def main():
    write = '--write' in sys.argv[1:]
    pending = json.load(open(PENDING, encoding='utf-8'))
    data = json.load(open(DATA, encoding='utf-8'))
    existing = {c['id'] for c in pending['cards']} | {d['id'] for d in data['deals']}
    new_id = promote.new_id(existing)

    draft = {
        'date': '2026-11-02',
        'title': '«Дом.РФ» выставил на торги проект КРТ в Воронеже',
        'ind': 'Недвижимость',
        'type': 'Продажа с торгов',
        'status': 'Обсуждается',
        'src': [['web:realty.ria.ru', 'https://realty.ria.ru/20261102/voronezh-2128671458.html']],
        'events': [],
        'seller': '«Дом.РФ»',
        'asset': 'проект комплексного развития территории (КРТ) в Воронеже',
        'sum': '136,96 млн ₽',
    }
    card = promote.to_card(draft, new_id)
    pending['cards'].append(card)

    state = json.load(open(STATE, encoding='utf-8'))
    state.get('decided_raw', {}).pop('d77717896', None)

    print('new_id=%s' % new_id)
    print(json.dumps(card, ensure_ascii=False, indent=1))
    if write:
        json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        json.dump(state, open(STATE, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('ЗАПИСАНО')
    else:
        print('Сухой прогон. Запись — с ключом --write.')


if __name__ == '__main__':
    main()
