# -*- coding: utf-8 -*-
"""Разрешение конфликта ребейза 24 ноября 2026 (~10:20 МСК) для
data/inbox/hold/2026-11-24.json ('drafts', ключ 'draft_id') через
merge_rebase_2026_11_19_09.merge_list. moderation_state.json и
deals_promoted.json разрешены вручную (простые, независимые добавления).
"""
import importlib.util
import json

ROOT = '/home/user/Compass'

spec = importlib.util.spec_from_file_location(
    'merge_rebase_2026_11_19_09', '%s/pipeline/merge_rebase_2026_11_19_09.py' % ROOT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def do(path, listkey, idkey):
    base = m.show(':1', path)
    ours = m.show(':2', path)
    theirs = m.show(':3', path)
    merged_items, conflicts = m.merge_list(base[listkey], ours[listkey], theirs[listkey], idkey)
    out = dict(ours)
    out[listkey] = merged_items
    with open('%s/%s' % (ROOT, path), 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('%s: %d записей, конфликтов: %d %s' % (path, len(merged_items), len(conflicts), conflicts))


if __name__ == '__main__':
    do('data/inbox/hold/2026-11-24.json', 'drafts', 'draft_id')
