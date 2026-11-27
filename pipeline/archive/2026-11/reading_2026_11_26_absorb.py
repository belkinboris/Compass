"""Вычитка 26.11.2026: заголовки gc23d6f1a и g8f548826 переписаны поверх записей
reread_2026_11_09_sj — отпечаток старых записей в proofread_absorbed."""
import json, sys
sys.path.insert(0, 'pipeline/ingest')
from review import fix_fingerprint
P = 'static/data/deals_promoted.json'
# `new` старых записей (reread_2026_11_09_sj, written_titles_std_c_2026_11_06).
OLD = {'gc23d6f1a': 'Неназванный покупатель купил у Halyk Bank Москоммерцбанк за 7,3 млрд тенге',
       'g8f548826': 'Неназванный партнер купил у ВТБ долю в «Росгосстрах Жизни»'}
WRONG = {'gc23d6f1a': 'Halyk Bank продал российскую «дочку» Москоммерцбанк неназванному покупателю за 7,3 млрд тенге'}
d = json.load(open(P))
for c in d['deals']:
    if c['id'] in OLD:
        assert c['title'] != OLD[c['id']]
        lst = c.setdefault('proofread_absorbed', {}).setdefault('title', [])
        if c['id'] in WRONG and fix_fingerprint(WRONG[c['id']]) in lst:
            lst.remove(fix_fingerprint(WRONG[c['id']])); print('drop wrong', c['id'])
        fp = fix_fingerprint(OLD[c['id']])
        if fp not in lst: lst.append(fp); print('absorb', c['id'])
if '--write' in sys.argv:
    json.dump(d, open(P, 'w'), ensure_ascii=False, indent=1); print('written')
