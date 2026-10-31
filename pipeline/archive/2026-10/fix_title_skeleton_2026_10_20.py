# -*- coding: utf-8 -*-
"""Дословность, 20 октября 2026: заголовок повторял скелет заголовка
источника почти дословно (verbatim_check.py --queue 40, 88% скелета у
РИА Недвижимость). Заголовок — поле структурное (review.py требует
дословного переноса, не годится для FIXES), поэтому правится прямым
скриптом с `assert` на старое значение.

    python3 pipeline/fix_title_skeleton_2026_10_20.py          # сухой прогон
    python3 pipeline/fix_title_skeleton_2026_10_20.py --write
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

TITLES = {
    # РИА Недвижимость: «Власти Москвы выставили на торги проект КРТ на месте Рижского рынка» — 88% скелета.
    'g22d3599c': ('Москва выставила на продажу право на застройку на месте Рижского рынка',
                  'Право на застройку участка с Рижским рынком выставлено на торги правительством Москвы'),
}


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))      # перечитано прямо перед записью
    by_id = {d['id']: d for d in data['deals']}
    for did, (old, new) in TITLES.items():
        d = by_id[did]
        assert d['title'] == old, (did, d['title'])
        d['title'] = new
        print('%s: %s\n        → %s' % (did, old, new))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
