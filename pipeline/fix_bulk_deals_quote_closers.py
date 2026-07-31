#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тот же дефект, что чинит `fix_nested_quote_closers.py`, но в `bulk_deals.json`.

«[Родовое слово] «[Имя]»» теряет вторую закрывающую «этажку»: «АО «Концерн
«Калашников» был назначен…» вместо «...«Калашников»» был назначен…». Тот же
файл — как правило, независимый источник данных со своим собственным
экземпляром дефекта, а не производная от `deals_promoted.json`; отдельный
файл, отдельный прогон проверки. Правило и самопроверки — те же, что в
`fix_nested_quote_closers.py` (см. его docstring).

Запуск:
    python3 pipeline/fix_bulk_deals_quote_closers.py            # сухой прогон
    python3 pipeline/fix_bulk_deals_quote_closers.py --write    # записать
"""
import json
import re
import sys

PATH = 'static/data/bulk_deals.json'
FIELDS = ('title', 'role', 'firm')
PATTERN = re.compile(r'«([^«»]{1,60}?)«([^«»]{1,60}?)»(?!»)')


def texts_flat(obj):
    out = []
    def w(o):
        if isinstance(o, str):
            out.append(o)
        elif isinstance(o, dict):
            for v in o.values():
                w(v)
        elif isinstance(o, list):
            for v in o:
                w(v)
    w(obj)
    return out


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))

    plan = []
    for i, d in enumerate(data):
        for field in FIELDS:
            t = d.get(field)
            if not t or t.count('«') <= t.count('»'):
                continue
            fixed, n = PATTERN.subn(lambda m: '«%s«%s»»' % (m.group(1), m.group(2)), t)
            assert n > 0, 'запись %d [%s]: разбалансировано, но пара «X «Y» не найдена: %r' % (i, field, t[:120])
            assert fixed.count('«') == fixed.count('»'), 'запись %d [%s]: всё ещё разбалансировано' % (i, field)
            plan.append((i, field, t, fixed))

    print('Полей с потерянной второй «этажкой»: %d' % len(plan))
    for i, field, old, new in plan:
        print('  запись %d [%s]' % (i, field))
        print('    было:  %s' % old[:130])
        print('    стало: %s' % new[:130])

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return

    for i, field, old, new in plan:
        assert data[i][field] == old, 'запись %d [%s]: изменилась с момента построения плана' % (i, field)
        data[i][field] = new
    for i, field, old, new in plan:
        assert data[i][field] == new, 'запись %d [%s]: не записалось' % (i, field)

    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('\nЗаписано: %d полей.' % len(plan))


if __name__ == '__main__':
    assert PATTERN.sub(lambda m: '«%s«%s»»' % (m.group(1), m.group(2)),
                        'ООО «Торговый дом "Меридиан"» работает') == \
        'ООО «Торговый дом "Меридиан"» работает', \
        'правило не должно трогать корректно вложенные кавычки (внутренние — прямые)'
    main('--write' in sys.argv)
