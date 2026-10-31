# -*- coding: utf-8 -*-
"""Отрасль g172b1374 («Первая нерудная компания», РЖД) — «Не определена»,
третья такая карточка при лимите два (test_industry_is_defined_except_...).
«Нерудная компания» — отраслевой термин (добыча нерудных строительных
материалов: песок, щебень, гравий), и профиль компании уже заведён с
ind «ГМК и добыча» (review.py.industry_is_supported) — но его стеблевое
сопоставление ловит только отличие в последних 1-3 буквах одного слова, а
у русской фразы падеж меняется во всех трёх словах («Первой нерудной
компании» -> «Первая нерудная компания»), так что review.py отклоняет
очевидную классификацию. Пишется этим скриптом напрямую.

Без --write — сухой прогон.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'static' / 'data' / 'deals_promoted.json'
ID = 'g172b1374'


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
