# -*- coding: utf-8 -*-
"""Поглотить записи FIXES, которые вычитка 13 ноября 2026 переписала мимо таблицы
(m106cb: c1659a21f/cc846f75c eco.share; m109c: gd39b4eaa sum — оценка эксперта снята,
«Не раскрыта»). Кладет отпечаток new каждой записи в proofread_absorbed; текст карточек
не меняет. Без --write — сухой прогон."""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import review  # noqa: E402
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
WANT = {('g6023c156', 'sum'), ('g6023c156', 'eco.sum'), ('c1659a21f', 'eco.val'), ('gd39b4eaa', 'sum'), ('gd39b4eaa', 'eco.sum'), ('cc846f75c', 'eco.share'), ('c1659a21f', 'eco.share')}
raw = open(BASE, encoding='utf-8').read(); data = json.loads(raw)
cards = {d['id']: d for d in data['deals']}
n = 0
for f in review.FIXES:
    key = (f['id'], f['field'])
    if key not in WANT or f['new'] is None:
        continue
    card = cards[f['id']]
    if review.get_field(card, f['field']) == f['new']:
        continue  # живая запись, совпадает с полем
    fp = review.fix_fingerprint(f['new'])
    lst = card.setdefault('proofread_absorbed', {}).setdefault(f['field'], [])
    if fp not in lst:
        lst.append(fp); n += 1
        print('поглощено', key, repr(f['new'])[:60])
print('отпечатков:', n)
if '--write' in sys.argv and n:
    out = json.dumps(data, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else '')
    open(BASE, 'w', encoding='utf-8').write(out); print('ЗАПИСАНО')
