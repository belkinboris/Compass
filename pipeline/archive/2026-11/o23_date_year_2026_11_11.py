# -*- coding: utf-8 -*-
"""Карточка g90767425 в очереди («О23» / Ozon): дата — годом.

Второе чтение, 11 ноября 2026: 11 ноября — день сообщения Ozon, а день, когда структуры
Чачавы утратили контроль над АО «О23», не назван ни в одном из пяти источников. По
docs/card_status_dates.md («Нет дня — только год») дата ставится годом; `date_basis`
(announcement) при дате-годе не нужен и снимается. `review.py` год не ставит.

    python3 pipeline/archive/2026-11/o23_date_year_2026_11_11.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
CID = 'g90767425'


def apply(pending):
    card = next(c for c in pending['cards'] if c['id'] == CID)
    if card['date'] == '2026' and 'date_basis' not in card:
        return False
    assert card['date'] == '2026-11-11', card['date']
    assert card.get('date_basis') == 'announcement', card.get('date_basis')
    card['date'] = '2026'
    del card['date_basis']
    return True


def main(write):
    raw = open(PENDING, encoding='utf-8').read()
    changed = apply(json.loads(raw))
    if not write:
        print('Сухой прогон: дата %s. Запись — с ключом --write.' % ('будет 2026' if changed else 'уже 2026'))
        return 0
    fresh_raw = open(PENDING, encoding='utf-8').read()
    fresh = json.loads(fresh_raw)
    if apply(fresh):
        with open(PENDING, 'w', encoding='utf-8') as f:
            f.write(json.dumps(fresh, ensure_ascii=False, indent=1) + ('\n' if fresh_raw.endswith('\n') else ''))
        print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv[1:]))
