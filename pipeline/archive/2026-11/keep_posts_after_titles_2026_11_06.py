# -*- coding: utf-8 -*-
"""Посты в канале не переписываются из-за разовой смены заголовков карточек (6 ноября 2026).

Стандарт заголовков касается карточки на сайте; пост в канале остается свободным (владелец,
6 ноября 2026). send_telegram.card_changes_since_post правит вышедший пост «молча», если заголовок
карточки отличается от снимка поста (`telegram_post_state[id].title`). У 136 карточек заголовок
переписан по стандарту — новых фактов нет, — поэтому снимок получает новый заголовок, а вышедший
пост остается как был. Остальные поля снимка не трогаются: настоящие изменения фактов по-прежнему
дойдут до поста.

    python3 pipeline/archive/2026-11/keep_posts_after_titles_2026_11_06.py [--write]
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def apply(base, before):
    od = {d['id']: d for d in before['deals']}
    ps = base.get('telegram_post_state') or {}
    n = 0
    for d in base['deals']:
        o = od.get(d['id'])
        if not o or o.get('title') == d.get('title'):
            continue
        snap = ps.get(d['id'])
        if snap and snap.get('title') == o.get('title'):
            snap['title'] = d.get('title')
            n += 1
    return n


def main(argv):
    rev = next((a for a in argv if not a.startswith('--')), 'HEAD~1')
    before = json.loads(subprocess.run(['git', 'show', rev + ':static/data/deals_promoted.json'], cwd=ROOT,
                                       capture_output=True, text=True).stdout)
    base = json.load(open(BASE, encoding='utf-8'))
    print('снимков к обновлению: %d' % apply(base, before))
    if '--write' not in argv:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    base = json.load(open(BASE, encoding='utf-8'))
    apply(base, before)
    with open(BASE, 'w', encoding='utf-8') as f:
        json.dump(base, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
