# -*- coding: utf-8 -*-
"""Карточки, у которых подошел срок проверки: через день, неделю и месяц после появления.

ЗАЧЕМ (27 ноября 2026). Сроки у каждой карточки свои (REVISION_BRIEF.md, «Три уровня
очереди»), но рутина «качество» считала очередь кусками кода из брифа и брала столько,
сколько успевала за 35 минут, — к 26 ноября накопилась 321 просроченная карточка.
Владелец: «каждая карточка должна иметь свой срок вычитки… главное, чтобы не копилось».
Теперь очередь считает этот скрипт, и рутина проверяет ВСЕ, что он выдал.

    python3 pipeline/reading_due.py            # сколько по уровням
    python3 pipeline/reading_due.py --ids day  # id уровня через запятую (day|week|month|all)
"""
import json
import os
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
# уровень: (есть отметка, нет отметки, дней от появления, отметка review.py)
TIERS = {'day': ('reviewed', 'deep_researched', 1, '--mark-deep'),
         'week': ('deep_researched', 'weekly_researched', 7, '--mark-weekly'),
         'month': ('weekly_researched', 'followup_researched', 30, '--mark-followup')}


def age_days(card, today):
    try:
        y, m, d = map(int, str(card.get('added'))[:10].split('-'))
        return (today - date(y, m, d)).days
    except Exception:
        return None


def due(base, today=None):
    today = today or date.today()
    out = {}
    for tier, (have, lack, days, _mark) in TIERS.items():
        rows = [c for c in base['deals'] if c.get(have) and not c.get(lack)
                and (age_days(c, today) or 0) >= days]
        rows.sort(key=lambda c: age_days(c, today) or 0, reverse=True)
        out[tier] = [c['id'] for c in rows]
    return out


def _self_check():
    base = {'deals': [{'id': 'a', 'added': '2026-11-01', 'reviewed': '2026-11-01'},
                      {'id': 'b', 'added': '2026-11-26', 'reviewed': '2026-11-26'},
                      {'id': 'c', 'added': '2026-11-01', 'reviewed': 1, 'deep_researched': 1},
                      {'id': 'd', 'added': '2026-10-01', 'reviewed': 1, 'deep_researched': 1, 'weekly_researched': 1}]}
    q = due(base, date(2026, 11, 27))
    assert q == {'day': ['a', 'b'], 'week': ['c'], 'month': ['d']}, q
    assert due(base, date(2026, 11, 26))['day'] == ['a']


def main(argv):
    _self_check()
    q = due(json.load(open(DATA, encoding='utf-8')))
    if '--ids' in argv:
        tier = argv[argv.index('--ids') + 1]
        print(','.join(sum(q.values(), []) if tier == 'all' else q[tier]))
        return
    for tier, ids in q.items():
        print('%-5s %3d  (отметка: review.py <id …> %s --write)' % (tier, len(ids), TIERS[tier][3]))
    print('всего %d' % sum(len(v) for v in q.values()))


if __name__ == '__main__':
    main(sys.argv[1:])
