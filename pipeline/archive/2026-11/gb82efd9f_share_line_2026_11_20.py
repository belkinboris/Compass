# -*- coding: utf-8 -*-
"""Применено 20 ноября 2026. «Медскан»/KDL (gb82efd9f): после привязки предмета к
профилю «Медскан Лаб» строка поста «Предмет» стала «Медскан Лаб — оставшиеся 51%…»:
первое предложение `eco.share` повторяло заголовок и выпадало. По правилу владельца
(12 ноября: «Предмет — юрлицо и доля») доля переписана одной записью с юрлицом.
Цитата: «продала… «стратегическому партнеру» 49% лабораторного бизнеса «KDL Медскан»…
После сделки «Медскан» сохранит контрольную долю в размере 51%» (зеркало РБК).

    python3 pipeline/archive/2026-11/gb82efd9f_share_line_2026_11_20.py [--write]
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OLD = '49% лабораторного бизнеса сети KDL. Оставшиеся 51% «Медскан» сохранил за собой.'
NEW = '49% лабораторного бизнеса KDL (ООО «Медскан Лаб»); 51% «Медскан» сохранил за собой.'
for rel, key in (('static/data/deals_promoted.json', 'deals'), ('static/data/pending.json', 'cards')):
    path = os.path.join(ROOT, rel)
    raw = open(path, encoding='utf-8').read(); d = json.loads(raw)
    c = [x for x in d[key] if x['id'] == 'gb82efd9f']
    if not c:
        continue
    assert c[0]['eco']['share'] == OLD, c[0]['eco']['share']
    c[0]['eco']['share'] = NEW
    if '--write' in sys.argv:
        open(path, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else ''))
    print(rel, 'ok')
