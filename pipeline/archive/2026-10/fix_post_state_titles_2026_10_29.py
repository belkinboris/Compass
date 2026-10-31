# -*- coding: utf-8 -*-
"""Снимки постов (`telegram_post_state`) с 29 октября 2026 помнят заголовок.
Старым снимкам заголовок дописывается текущим (ничего не править), а
g25a6766d (Baggins Coffee) — прежним «Сеть петербургских кофеен Baggins Coffee
продали»: пост 231 вышел с ним, и ближайший прогон публикации заменит его.
Без --write — сухой прогон."""
import io, json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
OLD = 'Сеть петербургских кофеен Baggins Coffee продали'

def main(write):
    data = json.load(io.open(DATA, encoding='utf-8'))
    titles = {d['id']: d.get('title') for d in data['deals']}
    state = data.get('telegram_post_state') or {}
    n = 0
    for did, snap in state.items():
        if isinstance(snap, dict) and 'title' not in snap and did in titles:
            snap['title'] = OLD if did == 'g25a6766d' else titles[did]
            n += 1
    assert state.get('g25a6766d', {}).get('title') == OLD, state.get('g25a6766d')
    print('снимков дополнено заголовком: %d; g25a6766d помнит прежний' % n)
    if write:
        json.dump(data, io.open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('записано')

if __name__ == '__main__':
    main('--write' in sys.argv)
