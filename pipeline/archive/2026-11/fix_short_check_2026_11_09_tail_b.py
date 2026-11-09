# -*- coding: utf-8 -*-
"""Короткая проверка 9 ноября 2026, хвост b: подпись издания в скобках в law.appr gd561d849.

`text_rules.py --changed` после apply_short_check_oneoff_2026_11_09.py: фраза «… оставил решение
в силе (Деловой Петербург, 12 декабря 2025 года).» — пометка о происхождении в скобках
(правило source_note). Издание названо в тексте, факт и дата те же.

    python3 pipeline/archive/2026-11/fix_short_check_2026_11_09_tail_b.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
OLD = ('Тринадцатый арбитражный апелляционный суд оставил решение в силе (Деловой Петербург, 12 декабря '
       '2025 года).')
NEW = ('По данным «Делового Петербурга», 12 декабря 2025 года стало известно, что Тринадцатый арбитражный '
       'апелляционный суд оставил решение в силе.')


def _apply(data):
    card = next(d for d in data['deals'] if d['id'] == 'gd561d849')
    appr = card['law']['appr']
    assert appr.count(OLD) == 1, appr
    card['law']['appr'] = appr.replace(OLD, NEW)
    return card['law']['appr']


if __name__ == '__main__':
    print(_apply(json.load(open(DATA, encoding='utf-8'))))
    if '--write' in sys.argv:
        fresh = json.load(open(DATA, encoding='utf-8'))
        _apply(fresh)
        json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('Записано.')
