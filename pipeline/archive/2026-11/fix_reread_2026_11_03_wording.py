# -*- coding: utf-8 -*-
"""Вычитка 3 ноября 2026: пять мелочей, которые приемка нашла уже в новых текстах партий.

«Сам/сама/сами» без нужды (plain_words) и предмет без «доли в» (share_form):
смысл и факты не меняются, только слово. Отпечатки записей FIXES этих полей —
в proofread_absorbed (поле переписано поверх примененной записи).
    python3 pipeline/archive/2026-11/fix_reread_2026_11_03_wording.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import review  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
EDITS = [  # id, поле, было (подстрока), стало
    ('g22000f22', 'eco.rationale', 'тем, что когда-то сам начинал карьеру', 'тем, что когда-то начинал карьеру'),
    ('g22000f22', 'extra', 'сам он готов помогать', 'Зуев готов помогать'),
    ('g4ff4b24c', 'eco.context', '— сами основатели,', '— основатели компании,'),
    ('gdab53817', 'eco.val', 'Сама компания оценивает себя', '«ИнвойсКафе» оценивает себя'),
    ('g6f4a071a', 'eco.share', '100% ООО «Хенкель Рус»', '100% доли в ООО «Хенкель Рус»'),
    ('gd4e555e3', 'eco.share', '49% ООО «Лаявожнефтегаз»', '49% доли в ООО «Лаявожнефтегаз»'),
]


def main(write=False):
    raw = open(DATA, encoding='utf-8').read()
    data = json.loads(raw)
    cards = {d['id']: d for d in data['deals']}
    for cid, field, old, new in EDITS:
        card = cards[cid]
        sec, key = field.split('.') if '.' in field else (None, field)
        holder = card[sec] if sec else card
        assert holder[key].count(old) == 1, (cid, field, holder[key])
        holder[key] = holder[key].replace(old, new)
        marks = card.setdefault('proofread_absorbed', {}).setdefault(field, [])
        for f in review.FIXES:
            if (f['id'], f['field']) == (cid, field) and f['new'] is not None:
                fp = review.fix_fingerprint(f['new'])
                if fp not in marks:
                    marks.append(fp)
        print('%s %s: %s → %s' % (cid, field, old, new))
    if write:
        open(DATA, 'w', encoding='utf-8').write(json.dumps(data, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else ''))
        print('записано')


if __name__ == '__main__':
    main('--write' in sys.argv)
