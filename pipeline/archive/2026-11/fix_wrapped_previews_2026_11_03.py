# -*- coding: utf-8 -*-
"""Снимки постов (`post_preview`) с текстом сообщения консоли — очистить
(3 ноября 2026: так ушли в каналы посты g7005cf1d, g03475792, g8f75eaf5).

    python3 pipeline/archive/2026-11/fix_wrapped_previews_2026_11_03.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path[:0] = [os.path.join(ROOT, 'pipeline', 'publish'), os.path.join(ROOT, 'pipeline'), ROOT]
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def main(argv):
    import format_post
    raw = open(BASE, encoding='utf-8').read()
    data = json.loads(raw)
    n = 0
    for d in data['deals']:
        p = d.get('post_preview')
        if p and ('[пост ' in p or 'Кнопки под постом' in p):
            d['post_preview'] = format_post.strip_console_wrapper(p).strip()
            assert '[пост ' not in d['post_preview'] and 'Кнопки под постом' not in d['post_preview']
            print(d['id']); n += 1
    if '--write' not in argv:
        print('Сухой прогон: %d. Запись — --write.' % n); return
    assert open(BASE, encoding='utf-8').read() == raw
    open(BASE, 'w', encoding='utf-8').write(json.dumps(data, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else ''))
    print('записано: %d' % n)


if __name__ == '__main__':
    main(sys.argv[1:])
