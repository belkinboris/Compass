# -*- coding: utf-8 -*-
"""Отрасль g98ad52f7 (АЛРОСА/«ГМК «Тимир»») — «Не определена», третья такая
карточка при лимите два (test_industry_is_defined_except_...). Профиль цели
уже заведён с ind «ГМК и добыча» (gbdba5da3) — тот же класс, что
pipeline/fix_g172b1374_ind.py: review.py.industry_is_supported() стеблевое
сопоставление по профилю компании ловит только отличие в последних буквах
последнего слова, а «ГМК «Тимир»» (многословное имя в кавычках) оно не
находит в цитате ни в каком падеже (KNOWN_ISSUES.md, 28 октября 2026).
Пишется этим скриптом напрямую.

Без --write — сухой прогон.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'static' / 'data' / 'deals_promoted.json'
ID = 'g98ad52f7'


def main(write):
    data = json.loads(DATA.read_text(encoding='utf-8'))
    card = next(c for c in data['deals'] if c['id'] == ID)
    assert card['ind'] == 'Не определена', card['ind']
    print('%s: ind %r -> %r' % (ID, card['ind'], 'ГМК и добыча'))

    if not write:
        print('Сухой прогон. Применение — с ключом --write.')
        return 0

    data = json.loads(DATA.read_text(encoding='utf-8'))
    card = next(c for c in data['deals'] if c['id'] == ID)
    assert card['ind'] == 'Не определена', card['ind']
    card['ind'] = 'ГМК и добыча'
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('Сделано.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
