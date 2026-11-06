# -*- coding: utf-8 -*-
"""geddb685d: карточка ушла в консоль (sweep.py --send) со снимком поста ДО
правки format_post.py (post_roles "Продавцы" вместо "Продавец" — находка
второго чтения). Снимаем draft_sent/post_draft_sent/post_preview, чтобы
send_drafts.py отправил карточку заново с верным текстом
(docs/intake_run.md, «Шаг 15: правка задела то, что владелец видел»).

Без ключа — сухой прогон; запись — --write (файл перечитывается перед записью).
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')

DEAL_ID = 'geddb685d'


def apply(data):
    n = 0
    for c in data['cards']:
        if c['id'] != DEAL_ID:
            continue
        if not any(c.get(k) for k in ('draft_sent', 'post_draft_sent', 'post_preview')):
            continue
        c.pop('draft_sent', None)
        c.pop('post_draft_sent', None)
        c.pop('post_preview', None)
        n += 1
        print('%s: draft_sent/post_draft_sent/post_preview сняты' % c['id'])
    return n


def main(write):
    apply(json.load(open(PENDING, encoding='utf-8')))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    data = json.load(open(PENDING, encoding='utf-8'))
    if apply(data):
        with open(PENDING, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
