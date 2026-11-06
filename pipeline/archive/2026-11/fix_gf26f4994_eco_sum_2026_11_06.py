# -*- coding: utf-8 -*-
"""gf26f4994 (очередь предпросмотра, «Сады Бештау»): eco.sum = цена торгов, как на «Обзоре». Запись — --write."""
import json, sys
P = 'static/data/pending.json'
WANT = {'gf26f4994': '247 млн ₽'}
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
