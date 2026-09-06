# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g6023c156` («ГК «Регион» продала Capital Group участок на юге Москвы»,
Закрыта) — дата стояла годом без месяца и дня («2022»), хотя источник
называет точный день.

Проверено ЛИЧНО прямым WebFetch (kommersant.ru/doc/5719027, уже стоял в
`src`, но использовался раньше только для факта о площади и продавце):
«Capital Group Павла Тё 8 декабря стала владельцем 100% ООО «Дикта-О»» —
статья опубликована 12.12.2022, то есть «8 декабря» — 2022 год (тот же
год, что уже стоял в карточке; переносится не новый год, а месяц и день
внутри уже известного).

Источник не в локальном кэше притока (проверено — сырья на диске для
этого адреса нет), поэтому правка идёт отдельным скриптом, а не через
таблицу FIXES review.py.

Запуск: python3 pipeline/fix_dikta_o_capital_group_exact_date.py
        python3 pipeline/fix_dikta_o_capital_group_exact_date.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g6023c156'

OLD_DATE = '2022'
NEW_DATE = '2022-12-08'


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['date'] == OLD_DATE

    print('=== date: станет ===')
    print(NEW_DATE)

    if write:
        deal['date'] = NEW_DATE
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
