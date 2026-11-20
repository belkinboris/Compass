# -*- coding: utf-8 -*-
"""Разрешение конфликта ребейза 20 ноября 2026 для
data/inbox/hold/2026-11-20.json, data/inbox/moderation_state.json и
static/data/pending.json — повторное использование логики
merge_rebase_2026_11_19_09.py.
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


def do_list(path, listkey, idkey, base_stage=':1'):
    try:
        base = show(base_stage, path)
    except Exception:
        base = {listkey: []}
    ours = show(':2', path)
    theirs = show(':3', path)
    merged_items, conflicts = m.merge_list(base[listkey], ours[listkey], theirs[listkey], idkey)
    out = dict(ours)
    out[listkey] = merged_items
    with open('%s/%s' % (ROOT, path), 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('%s: %d записей, конфликтов: %d %s' % (path, len(merged_items), len(conflicts), conflicts))
    return conflicts, base, ours, theirs


def do_moderation_state():
    path = 'data/inbox/moderation_state.json'
    base = show(':1', path)
    ours = show(':2', path)
    theirs = show(':3', path)
    out = {}
    all_conflicts = {}
    for k in set(base) | set(ours) | set(theirs):
        b, o, t = base.get(k, {}), ours.get(k, {}), theirs.get(k, {})
        if isinstance(o, list) or isinstance(t, list) or isinstance(b, list):
            out[k] = m.merge_list_of_scalars(b if isinstance(b, list) else [],
                                              o if isinstance(o, list) else [],
                                              t if isinstance(t, list) else [])
        else:
            merged, conflicts = m.merge_dict_of_dicts(b, o, t)
            out[k] = merged
            if conflicts:
                all_conflicts[k] = conflicts
    with open('%s/%s' % (ROOT, path), 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('%s: конфликтов: %s' % (path, all_conflicts or 'нет'))


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
    hc, hb, ho, ht = do_list('data/inbox/hold/2026-11-20.json', 'drafts', 'draft_id')
    if hc:
        print_conflict_detail(hc, hb, ho, ht, 'draft_id', 'drafts')
    do_moderation_state()
    pc, pb, po, pt = do_list('static/data/pending.json', 'cards', 'id')
    if pc:
        print_conflict_detail(pc, pb, po, pt, 'id', 'cards')
