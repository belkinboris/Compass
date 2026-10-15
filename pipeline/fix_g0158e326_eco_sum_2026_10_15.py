# -*- coding: utf-8 -*-
"""МГКЛ (g0158e326): `eco.sum` стоял прочерком, хотя `sum` («Обзор») уже
несёт «7–10 млрд ₽» — ровно случай, что держит
`test_the_sum_on_the_overview_is_the_sum_in_the_economist`
(`docs/card_money.md`: «sum и eco.sum — одно значение, рендер их не
связывает»). Ставит `eco.sum` тем же значением.

Без ключа — сухой прогон, запись по --write.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

OLD = '—'
NEW = '7–10 млрд ₽'


def main():
    write = '--write' in sys.argv
    data = json.load(open(DATA, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == 'g0158e326')
    assert card['sum'] == NEW, card['sum']
    assert card['eco']['sum'] == OLD, card['eco']['sum']
    card['eco']['sum'] = NEW
    print('g0158e326: eco.sum %r -> %r' % (OLD, NEW))
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
