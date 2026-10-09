"""Отметка «ждёт с» у трёх карточек очереди, заведённых 18 сентября мимо
promote.py (gd85b3ba8 Мадрид, g64462179 Nestlé, g2daf32fe «Ашан»): без неё
approve.py считал «0 ч из 24» и карточки не выходили по молчанию три недели.
Ставим момент починки: в канал они ушли бы как свежие (день появления
на сайте), поэтому владельцу даются обычные сутки на решение, а не
публикация задним числом от 18 сентября. Без --write —
сухой прогон."""
import json, sys
PATH = 'static/data/pending.json'
SINCE = '2026-10-09T13:02:16+00:00'
IDS = ('gd85b3ba8', 'g64462179', 'g2daf32fe')
write = '--write' in sys.argv
data = json.load(open(PATH, encoding='utf-8'))
for c in data['cards']:
    if c['id'] in IDS:
        assert not c.get('pending_since'), (c['id'], c.get('pending_since'))
        print(c['id'], '-> pending_since', SINCE)
        c['pending_since'] = SINCE
if write:
    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')
