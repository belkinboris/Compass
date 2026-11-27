"""g4ae30fd2: сумма 5 млрд ₽ (запись reread_2026_11_09_se и др.) заменена на 1 млрд ₽
записью reading_2026_11_27_indie_go — отпечаток старых записей в proofread_absorbed."""
import json, sys
sys.path.insert(0, 'pipeline/ingest')
from review import fix_fingerprint
P = 'static/data/deals_promoted.json'
d = json.load(open(P, encoding='utf-8'))
c = next(x for x in d['deals'] if x['id'] == 'g4ae30fd2')
assert c['sum'] == '1 млрд ₽'
for field in ('sum', 'eco.sum'):
    lst = c.setdefault('proofread_absorbed', {}).setdefault(field, [])
    fp = fix_fingerprint('5 млрд ₽')
    if fp not in lst: lst.append(fp); print('absorb', field)
if '--write' in sys.argv:
    json.dump(d, open(P, 'w', encoding='utf-8'), indent=1, ensure_ascii=False); print('written')
