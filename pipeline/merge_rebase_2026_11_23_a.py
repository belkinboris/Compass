# -*- coding: utf-8 -*-
"""Разрешение конфликта ребейза 23 ноября 2026 (приток, внеочередной прогон,
карточка g3976a960) для data/inbox/hold/2026-11-23.json,
data/inbox/moderation_state.json и static/data/pending.json — та же логика,
что в merge_rebase_2026_11_22_b.py."""
import importlib.util
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('merge_b', os.path.join(ROOT, 'merge_rebase_2026_11_22_b.py'))
merge_b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(merge_b)

if __name__ == '__main__':
    merge_b.do_list_doc('data/inbox/hold/2026-11-23.json', 'drafts', 'draft_id')
    merge_b.merge_a.do_moderation_state_raw_titles_aware()
    merge_b.do_list_doc('static/data/pending.json', 'cards', 'id')
