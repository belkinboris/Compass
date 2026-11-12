# -*- coding: utf-8 -*-
"""«Библио-Глобус»: одобрение совета директоров продавца — корпоративное, а не согласование
регулятора (владелец, 12 ноября 2026). Этап назван своим именем, статус карточки возвращен
в «Обсуждается» (договор не подписан), черновик поста снят для повторного показа."""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
d = json.load(open(DATA, encoding='utf-8'))
x = next(c for c in d['deals'] if c['id'] == 'g4afd35d0')
e = next(ev for ev in x['events'] if ev.get('kind') == 'approval')
NEW = 'Получено корпоративное одобрение'
if e.get('title') != NEW:
    assert e.get('title') == 'Согласование получено', e.get('title')
    assert x.get('status') == 'Согласование получено', x.get('status')
    e['title'] = NEW
    x['status'] = 'Обсуждается'
    if isinstance(e.get('snapshot'), dict):
        e['snapshot']['status'] = 'Обсуждается'
    e.pop('milestone_drafted_at', None)
    print('g4afd35d0: этап ->', NEW, '; статус -> Обсуждается')
    if '--write' in sys.argv:
        json.dump(d, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
else:
    print('уже исправлено')
