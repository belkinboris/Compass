# -*- coding: utf-8 -*-
"""Russ Outdoor/«Метроном» (`g3ef24264`): месячный дообыск нашёл третье
приобретённое юрлицо («Метротранс-Сервис», техобслуживание конструкций)
и предысторию консолидации транзитной рекламы (в 2021 году Russ Outdoor
уже купила nebo.digital и получила весь инвентарь московского метро —
факт лежит в уже процитированном источнике карточки, Коммерсанте, просто
не был перенесён раньше). Плюс вторую, расходящуюся с уже известной,
экспертную оценку суммы — обе оценки честно показывают разброс, а не
заменяют друг друга. `eco.context` и `eco.val` уже заняты — дословно
объединить с цитатами из ДРУГИХ источников `review.py` не может, правка
разовым скриптом.

Запуск: python3 pipeline/fix_russ_outdoor_metronom_context.py           # проверка
        python3 pipeline/fix_russ_outdoor_metronom_context.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g3ef24264'

OLD_CONTEXT = (
    'По данным ЕГРЮЛ, 20 июня головная структура Russ Outdoor — ООО '
    '«Стинн» — стала владельцем 100% долей оператора рекламы в '
    'петербургском метро ООО «Метроном» и эксклюзивного продавца этой '
    'рекламы ООО «Рекламное агентство `Проспект`», ранее принадлежавших '
    'известному игроку на рынке петербургской наружки Дмитрию Столову и '
    'его партнерам.')
NEW_CONTEXT = OLD_CONTEXT + (
    ' «Стинн» также приобрел компанию «Метротранс-Сервис», занимающуюся '
    'техобслуживанием рекламных конструкций подземки. В 2021 году Russ '
    'Outdoor купила 100% агентства nebo.digital, через которое '
    'размещается реклама в московском метро. В результате Russ Outdoor '
    'получила право размещать рекламу на всем инвентаре столичного '
    'метрополитена.')

OLD_VAL = (
    'Директор общероссийского сервиса бронирования наружной рекламы '
    'all-billboards Андрей Байдужий: «Сделки по покупке-продаже '
    'рекламных операторов обычно проходят по цене 8–12 EBITDA. То есть '
    'по международным стандартам оператор рекламы в питерском метро мог '
    'стоить 1,6–2 млрд руб.»')
NEW_VAL = OLD_VAL + (
    ' Оценки других изданий расходятся: «Сумма сделки могла составить '
    'до 2 млрд руб., считают аналитики, опрошенные изданием» (AdIndex), '
    'тогда как «по оценке экспертов ADPASS, сумма сделки не превысила '
    '1 млрд рублей».')

NEW_SRCS = [
    ['ADPASS', 'https://adpass.ru/russ-outdoor-poluchil-kontrol-nad-'
     'reklamoj-v-metro-peterburga/'],
    ['AdIndex', 'https://adindex.ru/news/marketing/2023/06/21/'
     '313388.phtml'],
]


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в базе' % CARD_ID
    assert card['eco'].get('context') == OLD_CONTEXT, (
        'eco.context изменился с ожидаемого: %r' % card['eco'].get('context'))
    assert card['eco'].get('val') == OLD_VAL, (
        'eco.val изменился с ожидаемого: %r' % card['eco'].get('val'))
    src = card.setdefault('src', [])
    print('ПРАВИМ  %s: eco.context — третье юрлицо и предыстория 2021 года' % CARD_ID)
    print('ПРАВИМ  %s: eco.val — расходящиеся оценки AdIndex/ADPASS' % CARD_ID)
    if write:
        card['eco']['context'] = NEW_CONTEXT
        card['eco']['val'] = NEW_VAL
        for s in NEW_SRCS:
            if s not in src:
                src.append(s)
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('ЗАПИСАНО')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
