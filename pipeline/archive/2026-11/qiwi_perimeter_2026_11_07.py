# -*- coding: utf-8 -*-
"""«Киви» (g0fadc207): периметр сделки шире предмета.

7 ноября 2026 предмет сделки перепривязан с КИВИ Банка на АО «Киви» (ИНН 7707510721,
fix_reread_profiles_a28_a29). Fusion Factor купил АО «Киви» вместе с КИВИ Банком, и
отчетность АО банк не покрывает, — мультипликатор по ней был бы неверным; золотая
выборка (test_gold_analytics, g0fadc207) держит, что сделка в расчет не идет.
Ставится `perimeter_beyond_target` (deal_multiples.admission → 'target_lot').

    python3 pipeline/archive/2026-11/qiwi_perimeter_2026_11_07.py [--write]
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def apply(data):
    d = next(x for x in data['deals'] if x['id'] == 'g0fadc207')
    assert d.get('target') == 'gd5d02d09' and 'Qiwi' in d['title'], (d.get('target'), d['title'])
    assert not d.get('perimeter_beyond_target')
    d['perimeter_beyond_target'] = True


def main(write):
    data = json.load(open(DATA, encoding='utf-8')); apply(data)
    print('g0fadc207: perimeter_beyond_target = True')
    if not write:
        print('Сухой прогон. Запись — с ключом --write.'); return 0
    data = json.load(open(DATA, encoding='utf-8')); apply(data)
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False); f.write('\n')
    print('ЗАПИСАНО.'); return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv[1:]))
