"""«Медси» (g4d7b2e19): заголовок по заметке партнёра владельца из консоли
(решение 885, 13 октября 2026): «Пусть в заголовке будет «Альфа-Банк купил
долю в Медси». Уже в предмете пишем конкретную долю». Текст поста он прислал
сам (решение 886) — его применит approve.py, здесь не трогаем.
Без ключа — сухой прогон, запись по --write."""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'static', 'data', 'pending.json')
OLD = 'Альфа-Банк купил 4,85% «Медси» у АФК «Система»'
NEW = 'Альфа-Банк купил долю в «Медси»'
raw = open(P, encoding='utf-8').read()
pending = json.loads(raw)
card = next(c for c in pending['cards'] if c['id'] == 'g4d7b2e19')
assert card['title'] == OLD, card['title']
card['title'] = NEW
print('g4d7b2e19: %s → %s' % (OLD, NEW))
if '--write' in sys.argv:
    out = json.dumps(pending, ensure_ascii=False, indent=1)
    if raw.endswith('\n'):
        out += '\n'
    open(P, 'w', encoding='utf-8').write(out)
    print('записано')
