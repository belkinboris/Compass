# -*- coding: utf-8 -*-
"""Синхронизация eco.sum с sum у g98ad52f7 (docs/card_money.md). review.py не
годится: eco.sum — не PROSE_WRITTEN, обычная дословность, а «16,1 млрд ₽» не
лежит дословно в цитате («16,1 миллиарда рублей») — то же число, другие слова.

Без --write — сухой прогон.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'static' / 'data' / 'pending.json'
ID = 'g98ad52f7'


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
