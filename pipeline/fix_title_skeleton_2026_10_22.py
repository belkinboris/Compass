# -*- coding: utf-8 -*-
"""Дословность, 22 октября 2026: три заголовка повторяли скелет заголовка
источника (verbatim_check.py --queue 40) — один и тот же указ о передаче
четырёх упаковочных компаний во временное управление «Центр Капиталу»,
разные источники, один и тот же шаблон «Активы Х переданы во временное
управление Y». Заголовок — поле структурное (review.py требует дословного
переноса, не годится для FIXES), поэтому правится прямым скриптом с
`assert` на старое значение.

    python3 pipeline/fix_title_skeleton_2026_10_22.py          # сухой прогон
    python3 pipeline/fix_title_skeleton_2026_10_22.py --write
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

TITLES = {
    'g8a599c40': ('Активы Tarkett в России переданы во временное управление «Центр Капиталу»',
                  'Указ забрал у Tarkett российские активы — временно управлять ими назначили «Центр Капитал»'),
    'g19410fc2': ('Активы «Каппа Рус» переданы во временное управление «Центр Капиталу»',
                  '«Каппа Рус» лишилась своих активов — временным управляющим назначен «Центр Капитал»'),
    'gfc3e1ae2': ('Активы «Онтэкс РУ» (бренд Helen Harper) переданы во временное управление «Центр Капиталу»',
                  'Активы бренда Helen Harper («Онтэкс РУ») на время перешли под контроль «Центр Капитала»'),
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
        f.write('\n')
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
