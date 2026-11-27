"""gaa5d4eb6: заголовок «ГК «ССК» купила…» (запись written_gaa5d4eb6_2026_11_09) заменен записью
owner_2026_11_27_gaa5d4eb6_title — отпечаток старой записи в proofread_absorbed."""
import json, sys
sys.path.insert(0, 'pipeline/ingest')
from review import fix_fingerprint
P = 'static/data/deals_promoted.json'
d = json.load(open(P, encoding='utf-8'))
c = next(x for x in d['deals'] if x['id'] == 'gaa5d4eb6')
assert 'ССК' not in c['title']
lst = c.setdefault('proofread_absorbed', {}).setdefault('title', [])
fp = fix_fingerprint('ГК «ССК» купила двух застройщиков группы «Носта»')
if fp not in lst:
    lst.append(fp); print('absorb')
if '--write' in sys.argv:
    json.dump(d, open(P, 'w', encoding='utf-8'), indent=1, ensure_ascii=False); print('written')
