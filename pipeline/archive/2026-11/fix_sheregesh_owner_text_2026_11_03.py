# -*- coding: utf-8 -*-
"""Шерегеш (g03475792), 3 ноября 2026, по «да» владельца: пост 253 владелец
удалил (ушел без его кнопки, с текстом консоли); его ответ на новый проект
поста — текст поста. Запись «пост вышел» снимается, текст владельца —
`post_override`, `post_approved`: публикация выпустит его ближайшим прогоном.

    python3 pipeline/archive/2026-11/fix_sheregesh_owner_text_2026_11_03.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path[:0] = [os.path.join(ROOT, 'pipeline', 'archive', '2026-11')]
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def main(argv):
    from post_sheregesh_owner_text_2026_11_03 import OWNER
    raw = open(BASE, encoding='utf-8').read()
    data = json.loads(raw)
    c = [d for d in data['deals'] if d['id'] == 'g03475792'][0]
    assert data['telegram_posts'].get('g03475792') == 253
    del data['telegram_posts']['g03475792']
    (data.get('telegram_post_state') or {}).pop('g03475792', None)
    c['post_override'] = OWNER
    c['post_approved'] = True
    print('g03475792: запись поста 253 снята, текст владельца, post_approved')
    if '--write' not in argv:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    assert open(BASE, encoding='utf-8').read() == raw
    open(BASE, 'w', encoding='utf-8').write(json.dumps(data, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else ''))
    print('записано')


if __name__ == '__main__':
    main(sys.argv[1:])
