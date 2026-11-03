# -*- coding: utf-8 -*-
"""g6be210fa (очередь предпросмотра): eco.sum = запрашиваемая цена, как на «Обзоре». Запись — --write."""
import json, sys
P = 'static/data/pending.json'
d = json.load(open(P, encoding='utf-8'))
card = [c for c in d['cards'] if c['id'] == 'g6be210fa'][0]
assert card['eco']['sum'] == '—' and card['sum'] == '220 млн ₽', (card['eco']['sum'], card['sum'])
if '--write' in sys.argv:
    card['eco']['sum'] = '220 млн ₽'
    json.dump(d, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('записано')
else:
    print('сухой прогон: eco.sum ->', '220 млн ₽')
