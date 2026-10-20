# -*- coding: utf-8 -*-
"""VEON/Perfectum (g28941fd8): `eco.sum` стоял прочерком, хотя `sum` («Обзор»)
уже несёт «$207 млн» — шестой случай того же пробела `accept_card.py`
(`sum_fields_differ` не ловит пустой `eco.sum`, только несовпадение двух
заполненных), записанного в KNOWN_ISSUES.md. Проверено заранее: записи
review.FIXES на это поле нет.

Без ключа — сухой прогон, запись по --write.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

OLD = '—'
NEW = '$207 млн'


def main():
    write = '--write' in sys.argv
    data = json.load(open(DATA, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == 'g28941fd8')
    assert card['sum'] == NEW, card['sum']
    assert card['eco']['sum'] == OLD, card['eco']['sum']
    card['eco']['sum'] = NEW
    print('g28941fd8: eco.sum %r -> %r' % (OLD, NEW))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('записано')
    return 0


if __name__ == '__main__':
    sys.exit(main())
