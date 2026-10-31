# -*- coding: utf-8 -*-
"""ga09376f6 («Экспанта»/«Стаксель») и g28941fd8 (VEON/Perfectum): приток
19 октября 2026 собрал и принял карточки, но send_drafts.py --write не
запустил — в консоль они попали только через кнопку «Что скоро выйдет»
(владелец видел их там с кнопками). Отмечаем карточки показанными, чтобы
send_drafts дослал только проекты постов, без повтора карточек.

    python3 pipeline/mark_shown_cards_2026_10_19.py --write
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
IDS = ('ga09376f6', 'g28941fd8')
data = json.load(open(PENDING, encoding='utf-8'))
for c in data['cards']:
    if c['id'] in IDS:
        assert not c.get('draft_sent') and c.get('accepted'), c['id']
        c['draft_sent'] = True
        c['post_draft_sent'] = False
if '--write' in sys.argv:
    with open(PENDING, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('записано')
else:
    print('сухой прогон')
