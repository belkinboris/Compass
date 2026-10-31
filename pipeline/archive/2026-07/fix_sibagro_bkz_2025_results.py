# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
gb43c8bcb («Сибагро» приобрела 51% Богдановичского комбикормового
завода) — судьба завода после приватизации не была отражена.
Проверено лично прямым WebFetch двух источников.

`eco.context` (заполнено, было «—»). Производственные показатели
выросли выше заявленных в 2025 году планов. Дословно (собственная
страница завода, sibagrogroup.ru): «368 600 тонн/год» комбикорма,
«16 600 тонн/год» премиксов, «7 700 тонн/год» БВМК — план на премиксы,
озвученный в январе 2025 года (aemcx.ru, цитата холдинга: «увеличить
выпуск премиксов до 12 тыс. тонн в год»), уже превышен. Финансовые
итоги 2025 года разнонаправлены: дословно (audit-it.ru): «В 2025 году
организация получила выручку в сумме 9,8 млрд руб., что на 3,6 млрд
руб., или на 58,8%, больше, чем годом ранее» — но «прибыль в размере
110 млн руб. Это на 85,1% меньше, чем в 2024 г.».

НЕ ВКЛЮЧЕНО: утверждение о доведении доли «Сибагро» в БКЗ до 100% —
единственный источник дал это агрегированным пересказом поисковика,
без прямой цитаты, и оно противоречит уже известной структуре
владения (76,07% после сделки) — не перенесено. Причина обвала прибыли
при росте выручки — не объяснена ни в одном источнике, не додумывается.
Консультанты сделки и судьба выручки Свердловской области от
приватизации — не найдены.

Запуск: python3 pipeline/fix_sibagro_bkz_2025_results.py
        python3 pipeline/fix_sibagro_bkz_2025_results.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gb43c8bcb'

OLD_CONTEXT = '—'
NEW_CONTEXT = (
    'К 2025 году завод превысил заявленные планы: производство '
    'достигло 368 600 тонн комбикорма, 16 600 тонн премиксов (план на '
    'январь 2025 года был 12 000 тонн) и 7700 тонн БВМК в год '
    '(sibagrogroup.ru). Выручка за 2025 год выросла на 58,8%, до 9,8 '
    'млрд руб., но чистая прибыль упала на 85,1%, до 110 млн руб. '
    '(audit-it.ru).'
)

NEW_SRC = [
    ['sibagrogroup.ru', 'https://sibagrogroup.ru/holding/companies/bogdanovichskiy-kombikormovyy-zavod-/'],
    ['audit-it.ru', 'https://www.audit-it.ru/contragent/1026600705790_ao-bogdanovichskiy-kombikormovyy-zavod'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, deal['eco']['context']
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('\n=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
