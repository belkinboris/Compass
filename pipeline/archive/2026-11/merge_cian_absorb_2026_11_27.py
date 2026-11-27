"""После слияния карточек «Циана» (merge_cian_cards_2026_11_27.py): прежние записи таблицы правок
на выжившую gd1bf6d5e описывали ее прежние значения («Назаров купил 21,97%»); теперь поля другие.
Отпечатки `new` этих записей — в proofread_absorbed, чтобы review.py не отказывал им и не возвращал
старые значения. Записи на g1a8709ea (удалена) сняты отдельно."""
import json, sys, importlib, pkgutil
sys.path.insert(0, 'pipeline/ingest')
import review
from review import fix_fingerprint
P = 'static/data/deals_promoted.json'
d = json.load(open(P, encoding='utf-8'))
card = next(c for c in d['deals'] if c['id'] == 'gd1bf6d5e')
n = 0
for m in sorted(x.name for x in pkgutil.iter_modules(['pipeline/ingest/fixes'])):
    for f in getattr(importlib.import_module('fixes.' + m), 'FIXES', []) or []:
        if f.get('id') != 'gd1bf6d5e' or f['field'] == 'src' or f['new'] is None:
            continue
        if review.already_applied(dict(f), card, d['companies']):
            continue
        lst = card.setdefault('proofread_absorbed', {}).setdefault(f['field'], [])
        fp = fix_fingerprint(f['new'])
        if fp not in lst:
            lst.append(fp); n += 1; print('absorb', m[-30:], f['field'])
print('отпечатков:', n)
if '--write' in sys.argv:
    json.dump(d, open(P, 'w', encoding='utf-8'), indent=1, ensure_ascii=False); print('written')
