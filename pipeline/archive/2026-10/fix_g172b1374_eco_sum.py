# -*- coding: utf-8 -*-
"""Синхронизация eco.sum с sum у g172b1374 (docs/card_money.md: одна и та же
цена в «Обзоре» и «Экономисте»). review.py не годится: eco.sum — не
PROSE_WRITTEN и не числовая SUM_BASES-проверка, а обычная дословность —
«1,9 млрд ₽» не лежит дословно в цитате («1,9 миллиарда рублей»), хотя это
то же число.

Без --write — сухой прогон.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'static' / 'data' / 'pending.json'
ID = 'g172b1374'


def main(write):
    data = json.loads(DATA.read_text(encoding='utf-8'))
    card = next(c for c in data['cards'] if c['id'] == ID)
    assert card['eco']['sum'] == '—', card['eco']['sum']
    print('%s: eco.sum %r -> %r' % (ID, card['eco']['sum'], card['sum']))

    if not write:
        print('Сухой прогон. Применение — с ключом --write.')
        return 0

    data = json.loads(DATA.read_text(encoding='utf-8'))
    card = next(c for c in data['cards'] if c['id'] == ID)
    assert card['eco']['sum'] == '—', card['eco']['sum']
    card['eco']['sum'] = card['sum']
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('Сделано.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
