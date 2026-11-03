# -*- coding: utf-8 -*-
"""gd73fd825: eco.share снова называет 100% (этапы в скобках). Запись — --write."""
import json, sys
P = 'static/data/deals_promoted.json'
OLD = '68% акций МКПАО «Яндекс» на первом этапе и оставшиеся примерно 28% — на втором.'
NEW = '100% акций МКПАО «Яндекс» (68% на первом этапе и оставшиеся примерно 28% — на втором).'
d = json.load(open(P, encoding='utf-8'))
card = [x for x in d['deals'] if x['id'] == 'gd73fd825'][0]
assert card['eco']['share'] == OLD, card['eco']['share']
if '--write' in sys.argv:
    card['eco']['share'] = NEW
    json.dump(d, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('записано')
else:
    print('сухой прогон: eco.share ->', NEW)
