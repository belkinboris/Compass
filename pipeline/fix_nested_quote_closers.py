#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Вложенное название теряет ВТОРУЮ закрывающую «этажку».

ЧТО СЛОМАНО. Часть юрлиц в базе называется по схеме «[родовое слово]
«[собственное имя]»» — «Санаторий «Россиянка»», «ТВК «Авиапарк»», «НПК
«Химпроминжиниринг»». У 39 карточек (80 полей: title/extra/eco/law) вторая
«этажка» потеряна: «Санаторий «Россиянка» — читатель не может понять, где
кончается название, и следующее слово в предложении выглядит его частью.

ПОЧЕМУ ЭТО НЕ ТА ЖЕ ПРАВКА, ЧТО В `fix_straight_quotes.py`. Там прямые
кавычки стояли ВМЕСТО «ёлочек» (стиль). Здесь стиль верный — не хватает
одного символа пунктуации: «этажка» открыта дважды (для родового слова и для
имени), а закрыта один раз. Признак — количество «, превышающее количество »
в пределах одного поля.

ГРАНИЦА ПРАВКИ. Правится только пара «слово «Имя» -> «слово «Имя»» — вставка
ровно одной », сразу после уже стоящей, когда перед ней есть НЕЗАКРЫТАЯ
внешняя «. Проверено на всех 39 карточках вручную (см. журнал прогона):
исключений с другой структурой не нашлось — каждая карточка либо содержит
именно эту пару, либо не совпадает вовсе (тогда скрипт остановится и покажет
поле, вместо того чтобы гадать).

Запуск:
    python3 pipeline/fix_nested_quote_closers.py            # сухой прогон
    python3 pipeline/fix_nested_quote_closers.py --write    # записать
"""
import json
import re
import sys

PATH = 'static/data/deals_promoted.json'

FIELDS = ['title', 'extra', 'sum']
NESTED = {'eco': ['rationale', 'share', 'target_fin', 'multiple', 'synergy', 'context', 'val', 'fin', 'finadv'],
          'law': ['structure', 'appr', 'terms']}

# «слово «Имя» (одна закрывающая) -> «слово «Имя»» (две). Ленивые группы и
# запрет « / » внутри них не дают захватить чужую, отдельно стоящую пару.
PATTERN = re.compile(r'«([^«»]{1,60}?)«([^«»]{1,60}?)»(?!»)')


def _get(deal, field):
    if '.' in field:
        block, sub = field.split('.', 1)
        return (deal.get(block) or {}).get(sub)
    return deal.get(field)


def _set(deal, field, value):
    if '.' in field:
        block, sub = field.split('.', 1)
        deal[block][sub] = value
    else:
        deal[field] = value


def texts(d):
    out = []
    for f in FIELDS:
        v = d.get(f)
        if v:
            out.append(f)
    for block, subs in NESTED.items():
        obj = d.get(block) or {}
        for s in subs:
            if obj.get(s):
                out.append('%s.%s' % (block, s))
    return out


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))

    plan = []
    for d in data['deals']:
        for field in texts(d):
            t = _get(d, field)
            no, nc = t.count('«'), t.count('»')
            if no <= nc:
                continue
            fixed, n = PATTERN.subn(lambda m: '«%s«%s»»' % (m.group(1), m.group(2)), t)
            assert n > 0, '%s.%s: разбалансировано («=%d, »=%d), но пара «X «Y» не найдена: %r' % (
                d['id'], field, no, nc, t[:120])
            no2, nc2 = fixed.count('«'), fixed.count('»')
            assert no2 == nc2, '%s.%s: после правки всё ещё разбалансировано' % (d['id'], field)
            plan.append((d['id'], field, t, fixed))

    print('Полей с потерянной второй «этажкой»: %d' % len(plan))
    for did, field, old, new in plan[:10]:
        print('  %-12s %-16s' % (did, field))
        print('    было:  %s' % old[:130])
        print('    стало: %s' % new[:130])
    if len(plan) > 10:
        print('  … и ещё %d' % (len(plan) - 10))

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return

    for d in data['deals']:
        for did, field, old, new in plan:
            if d['id'] != did:
                continue
            cur = _get(d, field)
            assert cur == old, '%s.%s: поле изменилось с момента построения плана' % (did, field)
            _set(d, field, new)

    for did, field, old, new in plan:
        deal = next(x for x in data['deals'] if x['id'] == did)
        assert _get(deal, field) == new, '%s.%s: не записалось' % (did, field)

    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('\nЗаписано: %d полей.' % len(plan))


if __name__ == '__main__':
    assert PATTERN.sub(lambda m: '«%s«%s»»' % (m.group(1), m.group(2)),
                        'ООО «Торговый дом "Меридиан"» работает') == \
        'ООО «Торговый дом "Меридиан"» работает', \
        'правило не должно трогать корректно вложенные кавычки (внутренние — прямые)'
    assert PATTERN.sub(lambda m: '«%s«%s»»' % (m.group(1), m.group(2)),
                        'Санаторий «Россиянка» и «Известия»') == \
        'Санаторий «Россиянка» и «Известия»', \
        'правило не должно трогать две отдельные, не вложенные друг в друга пары'
    main('--write' in sys.argv)
