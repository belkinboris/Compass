# -*- coding: utf-8 -*-
"""Заголовки двух постов об этапах — по стандарту заголовка (владелец, 12 ноября 2026:
«Что с заголовками»). Черновик снимается, чтобы send_milestone_drafts показал исправленный."""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
FIX = {('gmru-arnest-reckitt', 'closed'): ('Сделку по покупке подмосковного завода бытовой химии Reckitt группой «Арнест» закрыли',
                                           '«Арнест» завершил покупку подмосковного завода бытовой химии Reckitt'),
       ('g4afd35d0', 'approval'): ('Совет директоров Шереметьево дал добро на продажу 75% «Библио-Глобуса» структурам Wildberries почти за 40 млрд рублей',
                                   'Совет директоров Шереметьево одобрил продажу 75% «Библио-Глобуса» Wildberries & Russ примерно за 40 млрд рублей')}
d = json.load(open(DATA, encoding='utf-8'))
n = 0
for x in d['deals']:
    for e in x.get('events') or []:
        k = (x['id'], e.get('kind'))
        if k in FIX and e.get('headline'):
            old, new = FIX[k]
            if e['headline'] == new:
                continue
            assert e['headline'] == old, e['headline']
            e['headline'] = new
            e.pop('milestone_drafted_at', None)
            n += 1
            print(x['id'], '->', new)
if '--write' in sys.argv and n:
    json.dump(d, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('правок', n, '(запись — --write)' if '--write' not in sys.argv else '')
