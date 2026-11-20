# -*- coding: utf-8 -*-
"""Разрешение конфликта ребейза 20 ноября 2026 (пятый за день) для
data/inbox/hold/2026-11-20.json и data/inbox/moderation_state.json.
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


def do_hold():
    path = 'data/inbox/hold/2026-11-20.json'
    base = show(':1', path)
    ours = show(':2', path)
    theirs = show(':3', path)
    if isinstance(ours, list):
        merged, conflicts = m.merge_list(base, ours, theirs, 'id')
        write(path, merged)
        print('%s: %d записей, конфликтов: %d %s' % (path, len(merged), len(conflicts), conflicts))
        return
    out = {}
    all_conflicts = {}
    for k in set(base) | set(ours) | set(theirs):
        b, o, t = base.get(k), ours.get(k), theirs.get(k)
        if isinstance(o, list) or isinstance(t, list) or isinstance(b, list):
            out[k] = m.merge_list_of_scalars(b if isinstance(b, list) else [],
                                              o if isinstance(o, list) else [],
                                              t if isinstance(t, list) else [])
        elif isinstance(o, dict) or isinstance(t, dict) or isinstance(b, dict):
            merged, conflicts = m.merge_dict_of_dicts(b or {}, o or {}, t or {})
            out[k] = merged
            if conflicts:
                all_conflicts[k] = conflicts
        else:
            out[k] = o if o is not None else t
    write(path, out)
    print('%s: конфликтов: %s' % (path, all_conflicts or 'нет'))


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
    write(path, out)
    print('%s: конфликтов: %s' % (path, all_conflicts or 'нет'))


if __name__ == '__main__':
    do_hold()
    do_moderation_state()
