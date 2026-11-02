# -*- coding: utf-8 -*-
"""Пилот перечитки (2 ноября 2026): прежние записи FIXES на поля, которые
пилот переписал, учесть отпечатком в `proofread_absorbed` (docs/card_editing.md,
«Правка поля мимо таблицы синхронизирует запись»). Иначе две записи на одно
поле — `test_no_duplicate_fix_for_one_field` (gb92f7119 eco.val: запись из
архива октября и запись пилота).

    python3 pipeline/archive/2026-11/fix_pilot_reread_absorbed_2026_11_02.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import review  # noqa: E402

BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PILOT = ('g1d36d186', 'g6663f201', 'gc9ea6b08', 'g7bbe19c2', 'g56d19a38',
         'g489b4309', 'g53bd1536', 'g718e3d0e', 'gcf05509a', 'gb92f7119',
         # вторая десятка вычитки (партии c и d)
         'g2b1ff5cb', 'gcbf6e44b', 'g2b62ae77', 'g73dba9d6', 'g076af76a',
         'g5b4e85aa', 'g3c7dd2e2', 'ge816c5b4', 'g5e7d168d', 'gf66151c1')


def main(write):
    raw = open(BASE, encoding='utf-8').read()
    data = json.loads(raw)
    cards = {d['id']: d for d in data['deals']}
    n = 0
    for cid in PILOT:
        recs = {}
        for f in review.FIXES:
            if f['id'] == cid and f['field'] != 'src':
                recs.setdefault(f['field'], []).append(f)
        for field, rs in recs.items():
            marks = cards[cid].setdefault('proofread_absorbed', {}).setdefault(field, [])
            # прежние записи — и любая запись, чье поле разовый скрипт вычитки
            # потом переписал (g2b1ff5cb ind: архив ставил «ГМК и добыча»,
            # вычитка — «Машиностроение»)
            stale = [f for f in rs if not review.already_applied(f, cards[cid], data['companies'])]
            for f in rs[:-1] + [f for f in stale if f is rs[-1]]:
                fp = review.fix_fingerprint(f['new'])
                if fp not in marks:
                    marks.append(fp)
                    n += 1
                    print('%s %s: учтена прежняя запись' % (cid, field))
    if write and n:
        assert open(BASE, encoding='utf-8').read() == raw
        open(BASE, 'w', encoding='utf-8').write(json.dumps(data, ensure_ascii=False, indent=1) + '\n')
        print('записано')


if __name__ == '__main__':
    main('--write' in sys.argv)
