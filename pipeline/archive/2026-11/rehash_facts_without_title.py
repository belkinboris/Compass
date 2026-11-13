# -*- coding: utf-8 -*-
"""Отпечаток подтвержденных фактов без заголовка (13 ноября 2026, facts.card_hash).

Факт доли и прочитанный признак смены контроля хранят card_hash полей, по которым их читали.
Заголовок из отпечатка убран; чтобы уже подтвержденные факты не стали «устаревшими» из-за
смены формулы, их отпечаток пересчитывается — но только там, где он совпадает со старой
формулой на нынешней карточке (то есть факт действительно свежий).

    python3 pipeline/archive/2026-11/rehash_facts_without_title.py           # сухой прогон
    python3 pipeline/archive/2026-11/rehash_facts_without_title.py --write
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)
import facts  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def old_hash(deal, key):
    eco = deal.get('eco') or {}
    if key == 'stake':
        return facts._hash(deal.get('title'), eco.get('share'), deal.get('asset'), deal.get('stake_acquired'))
    return facts._hash(deal.get('type'), deal.get('title'), deal.get('status'))


d = json.load(open(DATA, encoding='utf-8'))
n = 0
for deal in d['deals']:
    f = deal.get('facts') or {}
    for key in ('stake', 'nature'):
        x = f.get(key)
        if isinstance(x, dict) and x.get('card_hash') and x['card_hash'] == old_hash(deal, key):
            new = facts.card_hash(deal, key)
            if new != x['card_hash']:
                x['card_hash'] = new
                n += 1
print('пересчитано отпечатков:', n)
if '--write' in sys.argv:
    json.dump(d, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('записано')
