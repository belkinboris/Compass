"""«Т-Технологии»/«Циан» (g9b4c2e71): этап 24 ноября 2026 — не «Переговоры»,
а направленная оферта (вид `offer`, владелец и партнер 25 ноября 2026: писать
как этап сделки).

    python3 pipeline/archive/2026-11/g9b4c2e71_offer_event.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))      # читается прямо перед записью
    deal = next(d for d in data['deals'] if d['id'] == 'g9b4c2e71')
    ev = [e for e in deal['events'] if e.get('date') == '2026-11-24']
    assert len(ev) == 1, len(ev)
    e = ev[0]
    if e.get('kind') == 'offer':
        print('уже исправлено')
        return
    assert e.get('kind') == 'negotiations' and e.get('title') == 'Переговоры', (e.get('kind'), e.get('title'))
    assert 'оферту' in e['note']
    e['kind'], e['title'] = 'offer', 'Оферта направлена'
    print('этап 2026-11-24: negotiations -> offer')
    if write:
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    else:
        print('сухой прогон')


if __name__ == '__main__':
    main('--write' in sys.argv)
