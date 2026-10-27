# -*- coding: utf-8 -*-
"""Дословность, 21 октября 2026: заголовок повторял заголовок источника
дословно (verbatim_check.py --queue 40, 100% скелета у Интерфакса).
Заголовок — поле структурное (review.py требует дословного переноса, не
годится для FIXES), поэтому правится прямым скриптом с `assert` на старое
значение.

    python3 pipeline/fix_title_skeleton_2026_10_21.py          # сухой прогон
    python3 pipeline/fix_title_skeleton_2026_10_21.py --write
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

TITLES = {
    # Интерфакс: «VEON покупает 100% мобильного оператора Perfectum в Узбекистане за $207 млн» — 100% скелета.
    'g28941fd8': ('VEON покупает 100% мобильного оператора Perfectum в Узбекистане за $207 млн',
                  'Узбекский мобильный оператор Perfectum полностью (100%) перешел VEON за $207 млн'),
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
