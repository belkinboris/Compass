# -*- coding: utf-8 -*-
"""Заметка 506 (консоль, 4 сентября 2026): «Разбиваем на 2 события»,
отвечая на карточку `gf0ce42ac» (выход Михаила Федяева из капитала ГК
«Азот»).

`eco.context» уже нёс оба шага прозой одним абзацем: (1) ещё до
закрытия сделки Федяев передал долю сестре Светлане Рыбальченко
(~март 2025 года, дата в источнике не названа точно), (2) сделка
закрылась 28 мая 2026 года иначе, чем предполагалось — Александр Орехов
довёл долю до 100%, Рыбальченко вышла. Владелец попросил разбить это на
два события в «Ходе сделки» — `events[]`, список, недоступный для
review.py/FIXES, поэтому одноразовый скрипт.

Запуск: python3 pipeline/fix_fedyaev_azot_split_two_events.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gf0ce42ac'

NEW_EVENTS = [
    {
        'kind': 'signed',
        'date': '2025-03-14',
        'title': 'Доля Федяева передана сестре, Светлане Рыбальченко',
        'note': ('Ещё до закрытия сделки с Ореховым Михаил Федяев передал '
                 'долю сестре: собственником 100% АО «Азот Инвест» стала '
                 'Светлана Рыбальченко. Юрист связывал это с опасением '
                 'санкций — партнёр Федяева Роман Троценко уже был под '
                 'санкциями ЕС и Британии.'),
        'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/7566990'],
    },
    {
        'kind': 'closed',
        'date': '2026-05-28',
        'title': 'Александр Орехов довёл долю в ГК «Азот» до 100%',
        'note': ('Сделка закрылась иначе, чем предполагалось изначально: '
                 'Александр Орехов увеличил долю в ГК «Азот» с 60% до '
                 '100%, а Светлана Рыбальченко, владевшая 40%, из '
                 'капитала вышла. Орехов и Троценко ранее были '
                 'совладельцами ИК «АЕОН».'),
        'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/8693027'],
    },
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {c['id']: c for c in data['deals']}
    card = by_id[CARD_ID]
    assert not card.get('events'), card.get('events')
    card['events'] = NEW_EVENTS
    print(f'{CARD_ID}: добавлены два события (передача сестре -> продажа Орехову)')

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Записано.')
    else:
        print('(сухой прогон, для записи — --write)')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
