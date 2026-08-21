# -*- coding: utf-8 -*-
"""PVH/Calvin Klein/Tommy Hilfiger/Денис Щукин (`gad807a24`): месячный
дообыск нашёл первый конкретный, подтверждённый документами шаг к
возможному возвращению бренда — заявка на регистрацию товарного знака
«cK» подана в Роспатент в июне 2025 года, одобрена в июне 2026-го (РИА
Новости/«Прайм», источник новый). `eco.context` уже занято фактом про
Дениса Щукина из другого источника — дословно объединить в одну цитату
для `review.py` нельзя, поэтому факт добавляется вторым предложением
разовым скриптом, тем же приёмом, что и остальные точечные правки этого
прогона.

Запуск: python3 pipeline/fix_pvh_trademark_return_context.py           # проверка
        python3 pipeline/fix_pvh_trademark_return_context.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gad807a24'
OLD_CONTEXT = (
    'В профиле Дениса Щукина в LinkedIn сказано, что с 2018 года он '
    'занимает должность директора розничной сети PVH в России, до '
    'того работал в местном офисе Adidas.')
NEW_CONTEXT = OLD_CONTEXT + (
    ' Согласно данным Роспатента, заявка на регистрацию товарного '
    'знака «cK» поступила в ведомство в июне 2025 года, а в июне '
    '2026-го Роспатент принял положительное решение о регистрации — '
    'под товарным знаком модный дом сможет продавать в России одежду, '
    'обувь, косметику и другие товары.')
SRC_ENTRY = ['ПРАЙМ', 'https://1prime.ru/20260606/rossija-870546626.html']


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в базе' % CARD_ID
    assert card['eco'].get('context') == OLD_CONTEXT, (
        'eco.context изменился с ожидаемого: %r' % card['eco'].get('context'))
    src = card.setdefault('src', [])
    print('ПРАВИМ  %s: eco.context — регистрация товарного знака «cK»' % CARD_ID)
    if write:
        card['eco']['context'] = NEW_CONTEXT
        if SRC_ENTRY not in src:
            src.append(SRC_ENTRY)
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('ЗАПИСАНО')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
