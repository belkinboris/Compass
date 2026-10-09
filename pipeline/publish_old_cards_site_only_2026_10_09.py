"""Мадрид (gd85b3ba8), Nestlé (g64462179), «Ашан» (g2daf32fe) — решение
владельца 9 октября 2026: «в канал не надо, в канал только свежие сделки;
на сайт отправляй». Ставим `no_post` (approve.py переносит его в базу,
send_telegram засевает telegram_posts как бэклог без поста) и возвращаем
`pending_since` к 18 сентября — сутки молчания давно прошли, ближайшая
публикация выложит их на сайт. Без --write — сухой прогон."""
import json, sys
PATH = 'static/data/pending.json'
IDS = ('gd85b3ba8', 'g64462179', 'g2daf32fe')
OLD = '2026-10-09T13:02:16+00:00'
SINCE = '2026-09-18T06:15:01+00:00'
write = '--write' in sys.argv
data = json.load(open(PATH, encoding='utf-8'))
seen = 0
for c in data['cards']:
    if c['id'] in IDS:
        assert c.get('pending_since') == OLD, (c['id'], c.get('pending_since'))
        assert not c.get('no_post'), c['id']
        c['pending_since'] = SINCE
        c['no_post'] = True
        seen += 1
        print(c['id'], '-> no_post, pending_since', SINCE)
assert seen == 3, seen
if write:
    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')
