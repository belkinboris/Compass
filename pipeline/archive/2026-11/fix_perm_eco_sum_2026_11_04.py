# -*- coding: utf-8 -*-
"""g4e184429, g90784f0a (очередь предпросмотра): eco.sum = запрашиваемая цена, как на «Обзоре». Запись — --write."""
import json, sys
P = 'static/data/pending.json'
WANT = {'g4e184429': '400 млн ₽', 'g90784f0a': '90 млн ₽'}
d = json.load(open(P, encoding='utf-8'))
for c in d['cards']:
    if c['id'] in WANT:
        assert c['eco']['sum'] == '—' and c['sum'] == WANT[c['id']], (c['id'], c['eco']['sum'], c['sum'])
        if '--write' in sys.argv:
            c['eco']['sum'] = WANT[c['id']]
        print(c['id'], 'eco.sum ->', WANT[c['id']])
if '--write' in sys.argv:
    json.dump(d, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('записано')
