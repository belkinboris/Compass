# -*- coding: utf-8 -*-
"""«Медси» (g4d7b2e19): заголовок по решению партнёра владельца из консоли
(решение 885, 13 октября 2026) — тот же заголовок, что `fix_medsi_title_by_
partner_2026_10_13.py` уже поставил в `pending.json`. Но карточка к моменту
того прогона уже была опубликована этой же рутиной (`approve.py --write`
перенёс её в `deals_promoted.json` раньше, чем другая сессия исправила
заголовок черновика) — правка легла туда, где карточки уже не было, и
осталась неприменённой к настоящей, опубликованной карточке. Применяет то
же решение к ней.

Без ключа — сухой прогон, запись по --write.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

OLD = 'Альфа-Банк купил 4,85% «Медси» у АФК «Система»'
NEW = 'Альфа-Банк купил долю в «Медси»'


def main():
    write = '--write' in sys.argv
    data = json.load(open(DATA, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == 'g4d7b2e19')
    assert card['title'] == OLD, card['title']
    card['title'] = NEW
    print('g4d7b2e19: %r -> %r' % (OLD, NEW))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('записано')
    return 0


if __name__ == '__main__':
    sys.exit(main())
