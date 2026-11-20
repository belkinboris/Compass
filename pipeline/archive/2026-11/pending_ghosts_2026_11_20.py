# -*- coding: utf-8 -*-
"""Применено 20 ноября 2026. В pending.json вернулись карточки, уже принятые в базу
(gfa56e747 «КВС»/«Невская мануфактура», g70cf2d0f ТЦ «Тура», g73b6378c ЗПИФ/Wildberries):
публикация в 05:55 UTC перенесла «КВС» в базу (12ed68a8), а прогон притока в 06:02
(8b80cbe0) записал очередь из старого снимка. Приток добавил к копии в очереди второй
источник, карточку показали заново, владелец одобрил — и approve.py упал на
«карточка уже в базе», остановив все решения публикации.
Источник из копии в очереди, которого нет в базе, переносится в карточку базы; копии
в очереди удаляются.

    python3 pipeline/archive/2026-11/pending_ghosts_2026_11_20.py [--write]
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PEND = os.path.join(ROOT, 'static', 'data', 'pending.json')

def run(write):
    rawd = open(DATA, encoding='utf-8').read(); rawp = open(PEND, encoding='utf-8').read()
    d = json.loads(rawd); p = json.loads(rawp)
    in_base = {x['id']: x for x in d['deals']}
    ghosts = [c for c in p['cards'] if c['id'] in in_base]
    for c in ghosts:
        b = in_base[c['id']]
        have = {s[1] if isinstance(s, list) and len(s) > 1 else str(s) for s in b.get('src') or []}
        for s in c.get('src') or []:
            url = s[1] if isinstance(s, list) and len(s) > 1 else str(s)
            if url not in have:
                b.setdefault('src', []).append(s); have.add(url)
                print('  %s: источник перенесен в базу — %s' % (c['id'], url))
        print('убираю из очереди копию %s «%s»' % (c['id'], c['title'][:60]))
    p['cards'] = [c for c in p['cards'] if c['id'] not in in_base]
    if write and ghosts:
        open(DATA, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=1) + ('\n' if rawd.endswith('\n') else ''))
        open(PEND, 'w', encoding='utf-8').write(json.dumps(p, ensure_ascii=False, indent=1) + ('\n' if rawp.endswith('\n') else ''))
        print('записано')
    return ghosts

run('--write' in sys.argv)
