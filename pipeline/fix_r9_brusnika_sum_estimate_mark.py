# -*- coding: utf-8 -*-
"""g6007df5d (Брусника/Level Group, Перовское шоссе): `sum` уже нёс верную
оценку («3–3,5 млрд ₽»), но без пометки «(по оценке)» — источник прямо
называет её оценкой консультанта Nikoliers, а не объявленной ценой:
«Директор департамента девелопмента земли Nikoliers Тимур Рывкин оценивает
стоимость 4 га на Перовском шоссе в 3–3,5 млрд руб.» (партия 5 агентов,
раунд 9, 15.08.2026).

ЗАПУСК:
    python3 pipeline/fix_r9_brusnika_sum_estimate_mark.py            # сухой прогон
    python3 pipeline/fix_r9_brusnika_sum_estimate_mark.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g6007df5d'
OLD = '3–3,5 млрд ₽'
NEW = '3–3,5 млрд ₽ (по оценке)'


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    deal = by_id[CARD_ID]

    assert deal.get('sum') == OLD, '%s: sum уже другой: %r' % (CARD_ID, deal.get('sum'))
    print('ПРАВИМ %s.sum: %r -> %r' % (CARD_ID, OLD, NEW))

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    deal['sum'] = NEW
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
