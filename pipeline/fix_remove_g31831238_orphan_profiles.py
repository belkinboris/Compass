# -*- coding: utf-8 -*-
"""g31831238 (Intel/Classiq) выкинута из очереди drop_pending.py: иностранная
сделка без российской стороны. Профили Intel (gcc906b40) и Classiq
(g54202bd3) заведены только для этой карточки и больше ничем не
используются (ни одной сделкой, ни match_keys) — удаляются как сироты.

Запуск: python3 pipeline/fix_remove_g31831238_orphan_profiles.py [--write]
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'
ORPHANS = {'gcc906b40': 'Intel', 'g54202bd3': 'Classiq'}


def check(data):
    for cid, name in ORPHANS.items():
        assert cid in data['companies'] and data['companies'][cid]['name'] == name, (cid, name)
        used = [d['id'] for d in data['deals']
                if d.get('buyer') == cid or d.get('seller_id') == cid
                or d.get('target') == cid or d.get('asset_id') == cid]
        assert not used, 'профиль %s использует сделка %s' % (cid, used)
        assert cid not in data.get('match_keys', {}), cid


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    check(data)
    if not write:
        print('сухой прогон: удалить профили %s' % list(ORPHANS))
        return
    data = json.load(open(PATH, encoding='utf-8'))
    check(data)
    for cid in ORPHANS:
        del data['companies'][cid]
    json.dump(data, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('записано: профили удалены — %s' % list(ORPHANS))


if __name__ == '__main__':
    main('--write' in sys.argv)
