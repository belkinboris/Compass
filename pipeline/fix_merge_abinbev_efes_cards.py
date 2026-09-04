# -*- coding: utf-8 -*-
"""Заметка 498 (консоль, 4 сентября 2026): «Сливаем и делаем вехи»,
отвечая на карточку `g0b733c0f» (AB InBev продаёт долю в AB InBev Efes
Anadolu Efes, объявлено 19.12.2023).

Сливает `g0311e96f» («Правкомиссия отказала Efes...», 20.06.2024) в
`g0b733c0f» — та же цель (`g25a20a64`), тот же продавец (AB InBev
текстом), покупатель — тот же реальный actor под двумя профилями
(«Anadolu Efes» и её SPV «Efes Breweries International» — оставлен
профиль Anadolu Efes, более узнаваемый и уже стоящий в первой
карточке). Уникальные факты `g0311e96f» (11 заводов, финансы 2023 года)
перенесены; вся хронология (два отказа правкомиссии, указ президента о
временном управлении, ребрендинг) оформлена как `events[]` — список,
недоступный для review.py/FIXES.

«Вехи» реализованы как события в «Ходе сделки» карточки, а НЕ как
`review.py --milestone`/посты в канал: это ретроспективные факты
2024–2025 годов, а не новое, только что подтверждённое событие — слать
их в канал сейчас значило бы выдать старые новости за свежие (см.
CLAUDE.md, «Одна сделка — один живой телеграм-пост»).

Запись FIXES для `g0311e96f» (`pipeline/ingest/fixes/
batch_agents100_r1.py`, поля eco.target_fin/eco.share) снята вместе с
карточкой.

Запуск: python3 pipeline/fix_merge_abinbev_efes_cards.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

SURVIVOR = 'g0b733c0f'
MERGED_AWAY = 'g0311e96f'

OLD_TARGET_FIN = (
    'В 2022 году выручка компании выросла на 14,2%, до 97,5 млрд ₽, а '
    'чистая прибыль — в 2,4 раза, до 12,1 млрд ₽.'
)
OLD_SHARE = 'Anadolu Efes станет единственным владельцем предприятия'
OLD_EXTRA = (
    'Сделка не состоялась: правительственная комиссия по контролю за '
    'осуществлением иностранных инвестиций дважды отклонила заявку (20 '
    'июня 2024 года и повторно в июне 2025 года). Указом президента РФ '
    'от 30 декабря 2024 года №1131 акции АО «АБ ИнБев Эфес» переданы во '
    'временное управление АО «Группа компаний Вместе»; с 1 сентября '
    '2025 года компания работает под именем «Напитки Вместе». Полная '
    'хронология — в отдельной карточке «Правкомиссия отказала Efes в '
    'покупке доли в AB InBev Efes».'
)

NEW_EVENTS = [
    {
        'kind': 'negotiations',
        'date': '2024-06-20',
        'title': 'Правкомиссия впервые отказала Efes в покупке доли',
        'note': ('Правительственная комиссия по контролю за осуществлением '
                 'иностранных инвестиций отказала Efes Breweries '
                 'International BV в покупке доли AB InBev в AB InBev Efes '
                 'BV. Причины отказа неизвестны.'),
        'source': ['РБК', 'https://www.rbc.ru/business/06/08/2024/66b0fffc9a7947a37a7814ca'],
    },
    {
        'kind': 'cancelled',
        'date': '2024-12-30',
        'title': 'Указ президента передал акции во временное управление',
        'note': ('Указом президента РФ от 30 декабря 2024 года №1131 '
                 '15,832 млрд обыкновенных и 92,943 тыс. привилегированных '
                 'акций АО «АБ ИнБев Эфес» переданы во временное управление '
                 'АО «Группа компаний «Вместе»».'),
        'source': ['Интерфакс', 'https://www.interfax.ru/business/1001317'],
    },
    {
        'kind': 'cancelled',
        'date': '2025',
        'title': 'Правкомиссия повторно отказала Efes',
        'note': 'В июне 2025 года Россия повторно отказала Anadolu Efes в выкупе доли AB InBev.',
        'source': ['Интерфакс', 'https://www.interfax.ru/business/1045201'],
    },
    {
        'kind': 'cancelled',
        'date': '2025-09-01',
        'title': 'Компания переименована в «Напитки Вместе»',
        'note': 'С 1 сентября 2025 года компания работает под новым коммерческим обозначением «Напитки Вместе».',
        'source': ['Интерфакс', 'https://www.interfax.ru/business/1045201'],
    },
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {c['id']: c for c in data['deals']}
    survivor = by_id[SURVIVOR]
    merged_card = by_id[MERGED_AWAY]

    assert survivor['eco']['target_fin'] == OLD_TARGET_FIN
    assert survivor['eco']['share'] == OLD_SHARE
    assert survivor['extra'] == OLD_EXTRA
    assert not survivor.get('events')

    survivor['eco']['target_fin'] = (
        OLD_TARGET_FIN + ' По итогам 2023 года выручка AB InBev Efes '
        'составила 108,6 млрд ₽, чистая прибыль — 16,7 млрд ₽. Компания '
        'произвела 23,2 млн гектолитров пива и 527 700 гектолитров '
        'кваса, сидра и воды.'
    )
    survivor['eco']['share'] = (
        OLD_SHARE + '. Компания владеет 11 заводами и тремя '
        'солодовенными комплексами в России.'
    )
    survivor['extra'] = (
        'Сделка не состоялась: правительственная комиссия по контролю за '
        'осуществлением иностранных инвестиций дважды отклонила заявку '
        '(20 июня 2024 года и повторно в июне 2025 года). Указом '
        'президента РФ от 30 декабря 2024 года №1131 акции АО «АБ ИнБев '
        'Эфес» переданы во временное управление АО «Группа компаний '
        '«Вместе»»; с 1 сентября 2025 года компания работает под именем '
        '«Напитки Вместе». Полная хронология — во вкладке «Ход сделки».'
    )
    survivor['events'] = NEW_EVENTS
    for label, url in merged_card['src']:
        if url not in {u for _, u in survivor['src']}:
            survivor['src'].append([label, url])

    data['merged'][MERGED_AWAY] = SURVIVOR
    data['deals'] = [c for c in data['deals'] if c['id'] != MERGED_AWAY]

    print(f'{MERGED_AWAY} слита в {SURVIVOR}, добавлено {len(NEW_EVENTS)} событий')

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Записано.')
    else:
        print('(сухой прогон, для записи — --write)')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
