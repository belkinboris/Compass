# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
gdc4ff4ab (Петр Жуков приобрел 34,96% доли в производителе напитков
Velle, 11.12.2023, статус «Закрыта») — заявленная интеграция с
«Фрутти» подтвердилась составом собственников, а не отдельным новым
юрлицом-холдингом; выручка Velle выросла, но не удвоилась.

Смена состава «Фрутти» — проверено лично прямым WebFetch (audit-it.ru,
ЕГРЮЛ): «Новый учредитель — Романовский Владислав Юрьевич» с датой
«24.12.2024», «Колобов Александр Григорьевич больше не числится в
ЕГРЮЛ учредителем» с той же датой — совладелец «Велле Холдинга»
Владислав Романовский заменил в «Фрутти» Александра Колобова
(владельца ГК «Шоколадница»).

НЕ ВКЛЮЧЕНО: точные показатели выручки за 2024 год (Velle 875,2 млн
₽, рост ~81% к 2022 году, но с убытком 154,8 млн ₽; «Фрутти» упала на
37,4% до 239,9 млн ₽) и общий гендиректор всех трёх структур — по
данным саб-агента из ЕГРЮЛ-агрегаторов (audit-it.ru, РБК Компании),
не дозаверено отдельным WebFetch в этом заходе; консолидация Петром
Жуковым 100% Indigo Capital Partners (апрель 2026, выкуп доли Марии
Минсковой) — отдельный факт о самом инвесторе, к сделке с Velle
прямого отношения не имеет, в карточку не добавляется.

Запуск: python3 pipeline/fix_zhukov_velle_frutti_integration.py
        python3 pipeline/fix_zhukov_velle_frutti_integration.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gdc4ff4ab'

OLD_EXTRA = (
    'Приобретение основателем Indigo Capital Partners Петра Жукова '
    '34,96% долей ООО «Велле Холдинг» — производителя растительных '
    'аналогов молока, йогуртов, каш и десертов под брендом Velle. '
    'Планируется интеграция компании в холдинг с компанией «Фрутти» '
    '(производитель напитков под маркой be true) и другими активами '
    'в стадии приобретения.'
)
NEW_EXTRA = OLD_EXTRA + (
    ' Интеграция подтвердилась составом собственников, а не отдельным '
    'юрлицом-холдингом: 24 декабря 2024 года совладелец «Велле '
    'Холдинга» Владислав Романовский вошёл в состав учредителей '
    '«Фрутти», заменив там Александра Колобова (владельца ГК '
    '«Шоколадница»).'
)

NEW_SRC = [
    ['audit-it.ru', 'https://www.audit-it.ru/contragent/1187746227151_ooo-frutti'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['extra'] == OLD_EXTRA

    new_src = deal['src'] + NEW_SRC

    print('=== extra: станет ===')
    print(NEW_EXTRA)
    print('\n=== src: добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['extra'] = NEW_EXTRA
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
