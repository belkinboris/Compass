"""Мадрид (gd85b3ba8), Nestlé (g64462179), «Ашан» (g2daf32fe): владелец
9 октября 2026 — «вставь нормально по дате, они слишком старые, будет тупо,
если они сверху будут». Лента сортирует по `added`; ставим его равным дате
сделки, approve.py сохранит заданный заранее `added`. Без --write — сухой
прогон."""
import json, sys
PATH = 'static/data/pending.json'
IDS = ('gd85b3ba8', 'g64462179', 'g2daf32fe')
write = '--write' in sys.argv
data = json.load(open(PATH, encoding='utf-8'))
seen = 0
for c in data['cards']:
    if c['id'] in IDS:
        assert 'added' not in c and c.get('no_post'), c['id']
        c['added'] = c['date']
        seen += 1
        print(c['id'], '-> added', c['added'])
assert seen == 3, seen
if write:
    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')
