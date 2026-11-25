"""Пост этапа g9b4c2e71-offer: строка «Предмет» по слову владельца (25 ноября
2026: «В предмете надо написать просто "потолок предложения - 100% акций
мкпао"») и повторный показ черновика в консоли.

    python3 pipeline/archive/2026-11/g9b4c2e71_offer_subject.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
NEW = 'Потолок предложения — 100% акций МКПАО «Циан»'


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))      # читается прямо перед записью
    deal = next(d for d in data['deals'] if d['id'] == 'g9b4c2e71')
    e = next(e for e in deal['events'] if e.get('id') == 'g9b4c2e71-offer')
    assert e['snapshot']['asset'].startswith('100% акций МКПАО «Циан» — таков потолок') or e['snapshot']['asset'] == NEW
    e['snapshot']['asset'] = NEW
    e.pop('milestone_drafted_at', None)                 # черновик уйдет в консоль заново
    print('предмет поста этапа: %s' % NEW)
    if write:
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    else:
        print('сухой прогон')


if __name__ == '__main__':
    main('--write' in sys.argv)
