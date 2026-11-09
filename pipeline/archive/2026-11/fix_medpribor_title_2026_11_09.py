# -*- coding: utf-8 -*-
"""Заголовок карточки gb89d3a84 — как владелец переписал пост (9 ноября 2026).

Владелец: «Что за название абсурдное? Посмотри, как я пост поменял, и в карте
название поменяй». Пост одобрен с текстом владельца (решение 1329), заголовок
поста — «АО «Медприбор» купило долю в ООО «ВТС»». Карточка еще в pending.json.

    python3 pipeline/archive/2026-11/fix_medpribor_title_2026_11_09.py [--write]
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
OLD = 'АО «Медприбор» купило у Александры Губы поставщика медтехники «ВТС»'
NEW = 'АО «Медприбор» купило долю в ООО «ВТС»'


def _apply(data):
    card = next(c for c in data['cards'] if c['id'] == 'gb89d3a84')
    assert card['title'] == OLD, card['title']
    card['title'] = NEW


def main(argv):
    _apply(json.load(open(PENDING, encoding='utf-8')))
    if '--write' not in argv:
        print('Сухой прогон: %s → %s' % (OLD, NEW))
        return 0
    fresh = json.load(open(PENDING, encoding='utf-8'))
    _apply(fresh)
    json.dump(fresh, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
