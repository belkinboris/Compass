# -*- coding: utf-8 -*-
"""Три карточки очереди (g8eb9ed40, g8317fa58, g9b4c2e71) прошли за день три круга
правок одних полей. При повторной записи review.py после сброса рабочей копии к
origin/main отпечатки средних записей цепочки не попали в proofread_absorbed —
test_ingest::test_no_duplicate_fix_for_one_field видит «две правки на одно поле».
Записи применялись по порядку (каждая — к результату предыдущей), поэтому все,
кроме последней, — поглощенные. Скрипт дописывает недостающие отпечатки.

    python3 pipeline/archive/2026-11/fix_absorbed_marks_three_2026_11_06.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import review  # noqa: E402

PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
IDS = {'gfd435463'}


def apply(pending):
    cards = {c['id']: c for c in pending['cards'] if c['id'] in IDS}
    added = []
    keys = {(f['id'], f['field']) for f in review.FIXES if f['id'] in IDS and f['field'] != 'src'}
    for key in sorted(keys):
        recs = [f for f in review.FIXES if (f['id'], f['field']) == key]
        if len(recs) < 2:
            continue
        card = cards[key[0]]
        current = review.fix_fingerprint(recs[-1]['new'])
        marks = card.setdefault('proofread_absorbed', {}).setdefault(key[1], [])
        for f in recs[:-1]:
            fp = review.fix_fingerprint(f['new'])
            if fp not in marks:
                marks.append(fp)
                added.append((key, fp))
        assert current, key
    return added


def main(argv):
    pending = json.load(open(PENDING, encoding='utf-8'))
    added = apply(pending)
    for a in added:
        print('  +', a)
    if '--write' not in argv:
        print('Сухой прогон: %d отпечатков. Запись — с ключом --write.' % len(added))
        return 0
    pending = json.load(open(PENDING, encoding='utf-8'))
    apply(pending)
    json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО: %d.' % len(added))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
