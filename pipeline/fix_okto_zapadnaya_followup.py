# -*- coding: utf-8 -*-
"""Группа ОКТО/«Западная Голд Майнинг» (`g15f35a5d`): месячный дообыск
нашёл переименование актива (ООО «А/С Западная» → ГОК «Кедровский»),
пятилетний производственный план (>6 т золота в год) и финансовые
результаты 2025 года — и материнской АО ГРК «Западная», и самого ГОК
«Кедровский» отдельно — из источников, отличных от уже занятых полей
`eco.context` и `eco.fin`. Слияние разовым скриптом.

Запуск: python3 pipeline/fix_okto_zapadnaya_followup.py           # проверка
        python3 pipeline/fix_okto_zapadnaya_followup.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g15f35a5d'

OLD_CONTEXT = (
    'В 2024 году предприятия холдинга произвели в совокупности менее '
    '3 т золота. Некоторое сокращение производства по сравнению с '
    'предыдущим годом руководство компании связывает со сложностями в '
    'приобретении и доставке запчастей, а также с дефицитом кадров. В '
    '2025 году предприятия ГК «Западная» в 2025 году планируют '
    'произвести 3,207 т золота.')
NEW_CONTEXT = OLD_CONTEXT + (
    ' Группа «ОКТО Золото» сменила название ООО «А/С Западная» на ГОК '
    '«Кедровский». Компания намерена создать предприятие с годовой '
    'добычей более шести тонн золота в год.')

OLD_FIN = ('В 2023 году компания добыла 3,4 тонны золота, чистая '
           'прибыль составила около 1,86 млрд рублей, выручка – 5,83 '
           'млрд рублей.')
NEW_FIN = OLD_FIN + (
    ' АО ГРК «Западная» в 2025 году увеличило чистую прибыль по РСБУ в '
    '7,79 раза до 7,869 млрд рублей — в основном за счёт 10,935 млрд '
    'рублей дивидендов от дочернего ООО «АС Западная» (рудник '
    '«Кедровский» в Бурятии); выручка от продаж выросла на 28,8%, до '
    '7,146 млрд рублей. Сам ГОК «Кедровский» (бывшая А/С «Западная») в '
    '2025 году увеличил выручку на 18,2% до 13,477 млрд рублей, прибыль '
    'от продаж — на 84,8% до 7,032 млрд рублей, чистую прибыль — на '
    '34,9% до 3,709 млрд рублей.')

NEW_SRCS = [
    ['НедраДВ', 'https://nedradv.ru/nedradv/ru/page_industry'
     '?obj=49c37832e6138f440d05d2a5f676c230'],
    ['НедраДВ', 'https://nedradv.ru/nedradv/ru/page_news'
     '?obj=bd23184a4151a5d68908f0107dbffe35'],
    ['Золото и технологии', 'https://zolteh.ru/news/'
     'okto_zoloto_pereimenovalo_a_s_zapadnaya_v_gok_kedrovskiy/'],
]


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в базе' % CARD_ID
    assert card['eco'].get('context') == OLD_CONTEXT, (
        'eco.context изменился с ожидаемого: %r' % card['eco'].get('context'))
    assert card['eco'].get('fin') == OLD_FIN, (
        'eco.fin изменился с ожидаемого: %r' % card['eco'].get('fin'))
    src = card.setdefault('src', [])
    print('ПРАВИМ  %s: eco.context — переименование и производственный план' % CARD_ID)
    print('ПРАВИМ  %s: eco.fin — финансы 2025 года (ГРК и ГОК «Кедровский»)' % CARD_ID)
    if write:
        card['eco']['context'] = NEW_CONTEXT
        card['eco']['fin'] = NEW_FIN
        for s in NEW_SRCS:
            if s not in src:
                src.append(s)
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('ЗАПИСАНО')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
