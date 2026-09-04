# -*- coding: utf-8 -*-
"""Заметка 495 (консоль, 4 сентября 2026): «Отдельная карточка, это
отдельная сделка на наш взгляд», отвечая на карточку `g9f76fe60» (Павел
Тё приобрел 25% Рязанской чаеразвесочной фабрики через ООО «СМ», ноябрь
2023 года).

`extra» карточки `g9f76fe60» уже нёс факт выхода (Коммерсантъ,
29.07.2025, kommersant.ru/doc/7923870, уже привязан вторым `src`):
подконтрольное Тё ООО «Велна» покинуло состав учредителей «СМ» — новыми
владельцами стали Максим Буре (90%) и Ольга Шатрова (10%). Осталась ли
сама доля РЧФ у «СМ» под новыми владельцами или перешла иначе — источник
не уточняет (уже отмечено как открытый вопрос в исходной карточке).

Запуск: python3 pipeline/fix_add_tyo_sm_exit_card.py [--write]
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ingest'))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

NEW_ID = 'g672c6dfe'
SM_ID = 'goooosm'


def main(write=False):
    import promote

    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    ids = {c['id'] for c in data['deals']}
    assert NEW_ID not in ids
    assert SM_ID not in data['companies']
    assert data['companies'].get('g4544d3b3', {}).get('name') == 'Павел Тё'

    data['companies'][SM_ID] = {
        'name': 'ООО «СМ»',
        'ind': 'Пищепром и напитки',
        'desc': ('Владеет 25%-й долей в ООО «Рязанская чаеразвесочная '
                 'фабрика». До июля 2025 года контролировалась Павлом Тё '
                 'через ООО «Велна».'),
        'kpi': ['Профиль', 'Автоматический'],
    }

    draft = {
        'date': '2025-07-29',
        'title': 'Павел Тё вышел из капитала ООО «СМ»',
        'ind': 'Пищепром и напитки',
        'type': 'M&A',
        'status': 'Закрыта',
        'buyer_name': 'Максим Буре и Ольга Шатрова',
        'src': [['Коммерсантъ', 'https://www.kommersant.ru/doc/7923870']],
    }
    card = promote.to_card(draft, NEW_ID)
    card['seller_id'] = 'g4544d3b3'
    card['target'] = SM_ID
    card['eco']['context'] = (
        'Подконтрольное Тё ООО «Велна» покинуло состав учредителей «СМ» '
        '29 июля 2025 года — новыми владельцами стали Максим Буре (90%) '
        'и Ольга Шатрова (10%). ООО «СМ» владеет 25%-й долей в ООО '
        '«Рязанская чаеразвесочная фабрика» (отдельная карточка '
        'g9f76fe60) — осталась ли эта доля у «СМ» под новыми владельцами '
        'или перешла иначе, источник не уточняет.'
    )

    data['deals'].append(card)
    print(f'Добавлена карточка {NEW_ID}: {card["title"]}')

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Записано.')
    else:
        print('(сухой прогон, для записи — --write)')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
