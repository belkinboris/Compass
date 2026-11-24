# -*- coding: utf-8 -*-
"""Разрешение конфликта main<->origin/main (14:5x МСК, 24 ноября 2026):
мой коммит (отсев не-сделок из очереди) и sweep.py (забор новостей) правили
те же файлы очереди в тот же час. Читает стадии :1/:2/:3 индекса (как
do_dup_or_hold/do_moderation_state в merge_rebase_2026_11_19_09.py) и пишет
результат в рабочее дерево — запускать прямо во время конфликтного merge,
до git add/commit."""
import importlib.util
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(ROOT, '..')
spec = importlib.util.spec_from_file_location(
    'merge_rebase_2026_11_19_09', os.path.join(ROOT, 'merge_rebase_2026_11_19_09.py'))
mr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mr)


def write(path, data):
    with open(os.path.join(REPO, path), 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write('\n')


def main():
    mr.do_dup_or_hold('data/inbox/hold/2026-11-24.json', 'drafts', 'draft_id')
    mr.do_moderation_state()

    path = 'static/data/pending.json'
    base = mr.show(':1', path)
    ours = mr.show(':2', path)
    theirs = mr.show(':3', path)
    merged_items, conflicts = mr.merge_list(base.get('cards', []), ours.get('cards', []),
                                             theirs.get('cards', []), 'id')
    out = dict(ours)
    out['cards'] = merged_items
    write(path, out)
    print('%s: %d карточек, конфликтов: %d %s' % (path, len(merged_items), len(conflicts), conflicts))


if __name__ == '__main__':
    main()
