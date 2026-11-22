# -*- coding: utf-8 -*-
"""Разрешение конфликта ребейза 22 ноября 2026 (приток, прогон ~05:20 МСК)
для data/inbox/hold/2026-11-22.json (add/add — оба прогона писали свой hold
того же дня) и data/inbox/moderation_state.json. Та же логика, что в
pipeline/merge_rebase_2026_11_19_09.py — переиспользуется через
importlib, не копируется."""
import importlib.util
import json
import os
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(ROOT)

spec = importlib.util.spec_from_file_location(
    'base_merge', os.path.join(ROOT, 'merge_rebase_2026_11_19_09.py'))
base_merge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base_merge)


def show(stage, path):
    out = subprocess.run(['git', 'show', '%s:%s' % (stage, path)], cwd=REPO,
                          capture_output=True, text=True).stdout
    return json.loads(out)


def do_moderation_state_raw_titles_aware():
    """Как base_merge.do_moderation_state(), но для `raw_titles` конфликт
    'sent' (sweep.py независимо показал то же сырье владельцу) против
    решения ('auto-drop'/'take'/'drop'/'enrich:...', приток независимо его
    разобрал) решается в пользу решения: 'sent' — это «показано», не
    вердикт, raw_screen.py сам не предлагает уже показанное к отсеву
    (`shown = {... if v == 'sent'}`), но если решение уже есть — оно
    финальнее отметки о показе, не наоборот."""
    path = 'data/inbox/moderation_state.json'
    try:
        base = show(':1', path)
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        base = {}
    ours = show(':2', path)
    theirs = show(':3', path)
    out = {}
    all_conflicts = {}
    for k in set(base) | set(ours) | set(theirs):
        b, o, t = base.get(k, {}), ours.get(k, {}), theirs.get(k, {})
        if isinstance(o, list) or isinstance(t, list) or isinstance(b, list):
            out[k] = base_merge.merge_list_of_scalars(
                b if isinstance(b, list) else [], o if isinstance(o, list) else [],
                t if isinstance(t, list) else [])
            continue
        if k == 'raw_titles':
            merged, conflicts = {}, []
            for ik in set(b) | set(o) | set(t):
                bi, oi, ti = b.get(ik), o.get(ik), t.get(ik)
                if oi == ti:
                    if oi is not None:
                        merged[ik] = oi
                elif bi == oi and ti is not None:
                    merged[ik] = ti
                elif bi == ti and oi is not None:
                    merged[ik] = oi
                elif oi == 'sent' and ti is not None:
                    merged[ik] = ti   # показ — не вердикт, решение финальнее
                elif ti == 'sent' and oi is not None:
                    merged[ik] = oi
                else:
                    conflicts.append(ik)
                    merged[ik] = oi if oi is not None else ti
            out[k] = merged
            if conflicts:
                all_conflicts[k] = conflicts
            continue
        merged, conflicts = base_merge.merge_dict_of_dicts(b, o, t)
        out[k] = merged
        if conflicts:
            all_conflicts[k] = conflicts
    with open('%s/%s' % (REPO, path), 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('%s: конфликтов: %s' % (path, all_conflicts or 'нет'))


def do_hold_add_add():
    path = 'data/inbox/hold/2026-11-22.json'
    ours = show(':2', path)
    theirs = show(':3', path)
    merged_items, conflicts = base_merge.merge_list([], ours['drafts'], theirs['drafts'], 'draft_id')
    out = dict(ours)
    out['drafts'] = merged_items
    with open('%s/%s' % (REPO, path), 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('%s: %d записей, конфликтов: %d %s' % (path, len(merged_items), len(conflicts), conflicts))


if __name__ == '__main__':
    do_hold_add_add()
    do_moderation_state_raw_titles_aware()
