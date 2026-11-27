"""G46, 27.11.2026: заголовок gb6d97747 (FLO/Reebok, статус «Закрыта») переписан поверх
записи reread_2026_11_09_sb — отпечаток ее `new` в proofread_absorbed."""
import json, sys
sys.path.insert(0, 'pipeline/ingest')
from review import fix_fingerprint
P = 'static/data/deals_promoted.json'
OLD = {('gb6d97747', 'title'): 'FLO Retailing собирается купить российскую сеть Reebok'}
d = json.load(open(P, encoding='utf-8'))
cards = {c['id']: c for c in d['deals']}
for (cid, field), val in OLD.items():
    lst = cards[cid].setdefault('proofread_absorbed', {}).setdefault(field, [])
    if fix_fingerprint(val) not in lst:
        lst.append(fix_fingerprint(val)); print('absorb', cid, field)
if '--write' in sys.argv:
    json.dump(d, open(P, 'w', encoding='utf-8'), indent=1, ensure_ascii=False); print('written')
