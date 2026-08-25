# -*- coding: utf-8 -*-
"""Карточка gc215d8b0 («Каппа РУС» приобрела Окуловскую бумажную
фабрику): перечитывание после правки (REVISION_BRIEF.md, «после правки —
перечитайте карточку целиком») нашло отрасль «Пищепром и напитки» —
неверную для производителя гофрокартона, тарного картона и бумажной
упаковки. В базе с 2 августа 2026 есть категория «Производство тары»
именно для таких компаний (см. урок CLAUDE.md про упаковку) — карточка
её не получила при первичном разборе.

Запуск: python3 pipeline/fix_okulovka_industry_category.py
        python3 pipeline/fix_okulovka_industry_category.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gc215d8b0'
OLD_IND = 'Пищепром и напитки'
NEW_IND = 'Производство тары'


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['ind'] == OLD_IND, 'ind изменился с момента чтения — проверьте'

    print('=== ind ===', OLD_IND, '->', NEW_IND)

    if write:
        deal['ind'] = NEW_IND
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
