# -*- coding: utf-8 -*-
"""Заметка 485 (консоль, 4 сентября 2026): «Отдельную карточку конечно
делаем», отвечая на карточку `g78e14953» (S8 Capital купила у Bridgestone
завод в Ульяновске, декабрь 2023).

Известная проблема (CLAUDE.md) держала находку на докладе саб-агента:
1 октября 2024 года весь холдинг «Кордиант» (в него входит и купленный
S8 Capital в 2023 году ульяновский завод) перепродан «Севергрупп»
Алексея Мордашова. Перепроверено прямым чтением в этом прогоне:

- Коммерсантъ (kommersant.ru/doc/7198179) — «Севергрупп» получила право
  собственности на активы ГК «Кордиант» с 1 октября 2024 года, сумма не
  раскрывается. В портфель входят бренды легковых шин Cordiant, Tunga,
  Torero, Gislaved и другие; на предприятиях работает около 8 тыс.
  человек.
- 73online.ru — бывший завод Bridgestone в Ульяновске перезапущен под
  брендом Gislaved осенью 2024 года (мощность 1,2 млн шин по итогам
  2025 года, вдвое больше в 2026-м).

Заведена новая карточка + профиль компании «ГК «Кордиант»» (сам холдинг
как предмет сделки, а не одна ульяновская площадка — сделка охватывает
все четыре завода группы: Ярославль, Омск, Калуга, Ульяновск).

Запуск: python3 pipeline/fix_add_severgroup_kordiant_card.py [--write]
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ingest'))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

NEW_ID = 'g7a3a83d1'
NEW_COMPANY_ID = 'gkordiant2024'


def main(write=False):
    import promote

    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    ids = {c['id'] for c in data['deals']}
    assert NEW_ID not in ids
    assert NEW_COMPANY_ID not in data['companies']
    assert data['companies'].get('g7ffb3b7a', {}).get('name') == 'Севергрупп'
    assert data['companies'].get('gffdff138', {}).get('name') == 'S8 Capital'

    data['companies'][NEW_COMPANY_ID] = {
        'name': 'ГК «Кордиант»',
        'ind': 'Автопром',
        'desc': ('Производитель шин, автокомпонентов и термотехники '
                 '(бренды Cordiant, Tunga, Torero, Gislaved); включает '
                 'заводы в Ярославле, Омске, Калуге и Ульяновске (бывший '
                 'завод Bridgestone). До октября 2024 года — структура '
                 'S8 Capital, затем перешла к «Севергрупп» Алексея '
                 'Мордашова.'),
        'kpi': ['Профиль', 'Автоматический'],
    }

    draft = {
        'date': '2024-10-01',
        'title': '«Севергрупп» купила производителя шин «Кордиант» у S8 Capital',
        'ind': 'Автопром',
        'type': 'M&A',
        'status': 'Закрыта',
        'src': [['Коммерсантъ', 'https://www.kommersant.ru/doc/7198179'],
                ['РБК',
                 'https://www.rbc.ru/business/02/10/2024/66fd06649a79475d0c280388'],
                ['73online.ru',
                 'https://73online.ru/r/milliarder_aleksey_mordashov_perezapustil_shinnyy_zavod_v_ulyanovske-147663']],
    }
    card = promote.to_card(draft, NEW_ID)
    card['buyer'] = 'g7ffb3b7a'
    card['seller_id'] = 'gffdff138'
    card['target'] = NEW_COMPANY_ID
    card['eco']['share'] = (
        'В портфель входят бренды легковых шин Cordiant, Tunga, Torero, '
        'Gislaved, грузовые шины Cordiant Professional и Tyrex, а также '
        'продукция «Метеор Авто», «Метеор Термо» и «Метеор Тех». На '
        'предприятиях работает около 8 тыс. человек.'
    )
    card['eco']['context'] = (
        'В группу входят заводы в Ярославле, Омске, Калуге и Ульяновске — '
        'бывший завод Bridgestone, купленный S8 Capital в декабре 2023 '
        'года (карточка g78e14953). Осенью 2024 года ульяновский завод '
        'перезапущен под брендом Gislaved: по плану на 2025 год — 1,2 млн '
        'шин, в 2026-м — вдвое больше.'
    )

    data['deals'].append(card)
    print(f'Добавлена карточка {NEW_ID}: {card["title"]}')
    print(f'Добавлен профиль {NEW_COMPANY_ID}: ГК «Кордиант»')

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Записано.')
    else:
        print('(сухой прогон, для записи — --write)')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
