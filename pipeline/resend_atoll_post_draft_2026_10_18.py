# -*- coding: utf-8 -*-
"""Показать в консоли проект поста «Атолл Капитал»/Aspace (ga5a7f3c1).

Карточка ушла в консоль 18 октября 2026 без поста: дата «2026», и
`format_post.is_fresh` не считал карточку очереди свежей (поправлено в
a599a3ad). Владелец попросил пост для канала «Компас - Недвижимость».
`send_drafts` шлёт проект поста, только если `post_draft_sent` ложно, а без
этого поля берёт `draft_sent` (True) — ставим False явно.

    python3 pipeline/resend_atoll_post_draft_2026_10_18.py --write
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
data = json.load(open(PENDING, encoding='utf-8'))
card = next(c for c in data['cards'] if c['id'] == 'ga5a7f3c1')
assert card.get('draft_sent') and not card.get('post_draft_sent')
card['post_draft_sent'] = False
if '--write' in sys.argv:
    with open(PENDING, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('post_draft_sent=False записан')
else:
    print('Сухой прогон')
