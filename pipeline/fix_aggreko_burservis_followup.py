# -*- coding: utf-8 -*-
"""Aggreko/«Аггреко Евразия»/БурСервис (`gc677124b`): месячный дообыск
нашёл дальнейшую M&A-активность покупателя — «БурСервис» продолжил
консолидацию нефтесервисного рынка и в феврале 2026 года купил 51%
производителя бурового оборудования «Уфабурмаш» (запись в ЕГРЮЛ от
13.02.2026), а также его финансовые показатели за 2024 год (масштаб
покупателя). Источник — Коммерсантъ, прочитан напрямую, не через
пересказ поисковика. `eco.context` уже занято другим предложением из
другого источника — дословно объединить для `review.py` нельзя, правка
разовым скриптом.

Запуск: python3 pipeline/fix_aggreko_burservis_followup.py           # проверка
        python3 pipeline/fix_aggreko_burservis_followup.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gc677124b'
OLD_CONTEXT = (
    'Напомним, в 2022 году Halliburton завершила продажу своего '
    'российского подразделения российской управленческой команде, '
    'состоящей из бывших сотрудников Halliburton. В результате '
    'Halliburton больше не ведёт операции в России. Находящаяся в '
    'России команда менеджеров стала владеть и управлять бывшим '
    'бизнесом и активами Halliburton в России под названием '
    'БурСервис, которое не зависит от Halliburton')
NEW_CONTEXT = OLD_CONTEXT + (
    '. «БурСервис» продолжил консолидацию нефтесервисного рынка: в '
    'феврале 2026 года (запись в ЕГРЮЛ от 13 февраля) компания стала '
    'владельцем 51% производителя нефтегазового оборудования '
    '«Уфабурмаш» — сделка, по оценке консультантов, снижает зависимость '
    'группы от зарубежных поставщиков бурового инструмента в условиях '
    'санкций. В 2024 году выручка самого «БурСервиса» выросла на '
    '21,1%, до 47,86 млрд руб., чистая прибыль — на 17%, до 14 млрд '
    'руб.')
NEW_SRC = ['Коммерсантъ', 'https://www.kommersant.ru/doc/8442557']


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в базе' % CARD_ID
    assert card['eco'].get('context') == OLD_CONTEXT, (
        'eco.context изменился с ожидаемого: %r' % card['eco'].get('context'))
    src = card.setdefault('src', [])
    print('ПРАВИМ  %s: eco.context — дальнейшая M&A-активность БурСервиса' % CARD_ID)
    if write:
        card['eco']['context'] = NEW_CONTEXT
        if NEW_SRC not in src:
            src.append(NEW_SRC)
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('ЗАПИСАНО')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
