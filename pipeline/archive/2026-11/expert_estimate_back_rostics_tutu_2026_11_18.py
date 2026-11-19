# -*- coding: utf-8 -*-
"""Оценка эксперта — в сумму (владелец, 18 ноября 2026): Rostic's и «Туту».

«Если специалисты давали оценку, то конечно должны писать в картах цену по оценке.
6-8 правильно написано было» (docs/card_money.md, «Что идет в сумму»).
  g1f2895c0 (IRB / 20% «Юниреста»): «Не раскрыта» -> «6–8 млрд ₽ (по оценке)» — Илья Шумов,
    «Коммерсантъ»; откат rostics_sum_undisclosed_2026_11_18.py.
  g5d3527dd («Туту» / «Ракета» и IBC): «Не раскрыта» -> «500–600 млн ₽ (по оценке)» — Михаил
    Бурмистров («Infoline-аналитика») оценивает две компании вместе; «600 млн ₽» из заголовка
    агрегатора остается в retracted.sum.

    python3 pipeline/archive/2026-11/expert_estimate_back_rostics_tutu_2026_11_18.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
EDITS = {'g1f2895c0': ('6–8 млрд ₽ (по оценке)', 'Шумов'), 'g5d3527dd': ('500–600 млн ₽ (по оценке)', 'Бурмистров')}


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))      # перечитано прямо перед записью
    for d in data['deals']:
        if d['id'] not in EDITS:
            continue
        new, who = EDITS[d['id']]
        if d['sum'] == new:
            print(d['id'], 'уже применено')
            continue
        assert d['sum'] == 'Не раскрыта' and d['eco']['sum'] == 'Не раскрыта', (d['id'], d['sum'])
        assert who in d['eco'].get('val', ''), (d['id'], 'оценщик должен быть назван в eco.val')
        d['sum'] = d['eco']['sum'] = new
        ret = (d.get('retracted') or {}).get('sum')
        if ret and new in ret:
            ret.remove(new)
        print('%s: Не раскрыта -> %s' % (d['id'], new))
    if write:
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
