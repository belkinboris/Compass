# -*- coding: utf-8 -*-
"""Две правки формы по замечаниям владельца и партнера (11 ноября 2026).

1. Сумма «(неофициально)» / «(неофициальная оценка)» → «(по оценке)»: владелец —
   «что за вординг „неофициально“, у нас же есть „по оценке“». Число не меняется.
2. Заголовок g995f83cf: «…у «Онэксима»» → «…у «Онэксим»» — партнер: «не надо склонять».

    python3 pipeline/archive/2026-11/sum_wording_and_oneksim_2026_11_11.py [--write]
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY, DAY = 'sum_wording_and_oneksim_2026_11_11', '2026-11-11'
SUMS = {'g0924279f': ('150–300 млн ₽ (неофициальная оценка)', '150–300 млн ₽ (по оценке)'),
        'ge370e8f1': ('35–40 млрд ₽ (неофициально)', '35–40 млрд ₽ (по оценке)'),
        'gaec5231e': ('300 млрд ₽ (неофициально)', '300 млрд ₽ (по оценке)')}
TITLE = ('g995f83cf', '«РКИП» купил «Ренессанс Капитал» у «Онэксима»', '«РКИП» купил «Ренессанс Капитал» у «Онэксим»')


def apply(data):
    by = {d['id']: d for d in data['deals']}
    for cid, (old, new) in SUMS.items():
        c = by[cid]
        assert c['sum'] == old, (cid, c['sum'])
        c['sum'] = new
        if (c.get('eco') or {}).get('sum') == old:
            c['eco']['sum'] = new
        fact_edit_guard.log(c, 'sum', new, 'Смена формы записи без смены числа: «%s» → «%s» (владелец: у нас принято «по оценке»).' % (old, new), '', BY, DAY)
        if (c.get('eco') or {}).get('sum') == new:
            fact_edit_guard.log(c, 'eco.sum', new, 'Та же смена формы записи, что в поле sum.', '', BY, DAY)
    c = by[TITLE[0]]
    assert c['title'] == TITLE[1], c['title']
    c['title'] = TITLE[2]
    fact_edit_guard.log(c, 'title', TITLE[2], 'Смена формы: название продавца в кавычках не склоняется (партнер владельца, 11 ноября 2026).', '', BY, DAY)


def main(write):
    raw = open(DATA, encoding='utf-8').read()
    old, data = json.loads(raw), json.loads(raw)
    apply(data)
    mass_edit_guard.check(old, data, os.environ.get('MASS_OK'))
    bad = fact_edit_guard.unbacked(old, data)
    assert not bad, bad
    if not write:
        print('Сухой прогон: 3 суммы и 1 заголовок. Запись — с ключом --write.')
        return 0
    fresh_raw = open(DATA, encoding='utf-8').read()
    fresh = json.loads(fresh_raw)
    apply(fresh)
    with open(DATA, 'w', encoding='utf-8') as f:
        f.write(json.dumps(fresh, ensure_ascii=False, indent=1) + ('\n' if fresh_raw.endswith('\n') else ''))
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv[1:]))
