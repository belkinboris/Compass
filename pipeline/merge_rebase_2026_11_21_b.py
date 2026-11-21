# -*- coding: utf-8 -*-
"""Разрешение конфликта ребейза 21 ноября 2026 (второй за прогон) для
static/data/pending.json.
"""
import importlib.util
import json
import subprocess

ROOT = '/home/user/Compass'

spec = importlib.util.spec_from_file_location(
    'merge_0919', '%s/pipeline/merge_rebase_2026_11_19_09.py' % ROOT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def show(stage, path):
    out = subprocess.run(['git', 'show', '%s:%s' % (stage, path)], cwd=ROOT,
                          capture_output=True, text=True).stdout
    return json.loads(out)


def write(path, obj):
    with open('%s/%s' % (ROOT, path), 'w', encoding='utf-8') as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)
        f.write('\n')


def do_pending():
    path = 'static/data/pending.json'
    base = show(':1', path)
    ours = show(':2', path)
    theirs = show(':3', path)
    merged_items, conflicts = m.merge_list(base['cards'], ours['cards'], theirs['cards'], 'id')
    out = dict(ours)
    out['cards'] = merged_items
    write(path, out)
    print('%s: %d карточек, конфликтов: %d %s' % (path, len(merged_items), len(conflicts), conflicts))
    return conflicts, base, ours, theirs


def print_conflict_detail(conflicts, base, ours, theirs, idkey, listkey):
    base_c = {c[idkey]: c for c in base[listkey]}
    ours_c = {c[idkey]: c for c in ours[listkey]}
    theirs_c = {c[idkey]: c for c in theirs[listkey]}
    for did in conflicts:
        b, o, t = base_c.get(did), ours_c.get(did), theirs_c.get(did)
        print('=== %s ===' % did)
        for k in (set(b or {}) | set(o or {}) | set(t or {})):
            bv, ov, tv = (b or {}).get(k), (o or {}).get(k), (t or {}).get(k)
            if bv != ov or bv != tv:
                print(' field %s | base: %r | ours: %r | theirs: %r' % (k, bv, ov, tv))


if __name__ == '__main__':
    pc, pb, po, pt = do_pending()
    if pc:
        print_conflict_detail(pc, pb, po, pt, 'id', 'cards')
