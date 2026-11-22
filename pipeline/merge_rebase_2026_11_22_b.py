# -*- coding: utf-8 -*-
"""Разрешение конфликта ребейза 22 ноября 2026 (приток, прогон ~11:20 МСК,
после долгого ожидания publication_busy.py) для data/inbox/hold/2026-11-22.json,
data/inbox/moderation_state.json (raw_titles-aware, см.
merge_rebase_2026_11_22_a.py) и static/data/pending.json ({"cards": [...]},
ключ 'id', та же логика merge_list, что для hold/duplicates)."""
import importlib.util
import json
import os
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(ROOT)

spec_a = importlib.util.spec_from_file_location(
    'merge_a', os.path.join(ROOT, 'merge_rebase_2026_11_22_a.py'))
merge_a = importlib.util.module_from_spec(spec_a)
spec_a.loader.exec_module(merge_a)
base_merge = merge_a.base_merge


def show(stage, path):
    out = subprocess.run(['git', 'show', '%s:%s' % (stage, path)], cwd=REPO,
                          capture_output=True, text=True).stdout
    return json.loads(out)


def do_list_doc(path, listkey, idkey):
    base = show(':1', path)
    ours = show(':2', path)
    theirs = show(':3', path)
    merged_items, conflicts = base_merge.merge_list(base[listkey], ours[listkey], theirs[listkey], idkey)
    out = dict(ours)
    out[listkey] = merged_items
    with open('%s/%s' % (REPO, path), 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('%s: %d записей, конфликтов: %d %s' % (path, len(merged_items), len(conflicts), conflicts))


if __name__ == '__main__':
    do_list_doc('data/inbox/hold/2026-11-22.json', 'drafts', 'draft_id')
    merge_a.do_moderation_state_raw_titles_aware()
    do_list_doc('static/data/pending.json', 'cards', 'id')
