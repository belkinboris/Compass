# -*- coding: utf-8 -*-
"""g7005cf1d (очередь предпросмотра): eco.sum = стартовая цена лота, как на «Обзоре». Запись — --write."""
import json, sys
P = 'static/data/pending.json'
d = json.load(open(P, encoding='utf-8'))
card = [c for c in d['cards'] if c['id'] == 'g7005cf1d'][0]
assert card['eco']['sum'] == '—' and card['sum'] == '15,275 млн ₽', (card['eco']['sum'], card['sum'])
if '--write' in sys.argv:
    card['eco']['sum'] = '15,275 млн ₽'
    json.dump(d, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('записано')
else:
    print('сухой прогон: eco.sum ->', '15,275 млн ₽')
