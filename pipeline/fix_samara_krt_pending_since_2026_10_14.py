# -*- coding: utf-8 -*-
"""Карточка g420352ff собрана разовым скриптом мимо promote.py (тот же
класс пропуска, что уже чинился для Мадрида/Nestlé/«Ашана», CLAUDE.md) —
у нее не было `pending_since`, от которого `approve.py` считает сутки
молчания владельца (test_data.py::test_every_pending_card_has_pending_since).

Запуск:
    python3 pipeline/fix_samara_krt_pending_since_2026_10_14.py            # сухой прогон
    python3 pipeline/fix_samara_krt_pending_since_2026_10_14.py --write    # применить
"""
import json
import sys
from datetime import datetime, timezone

PENDING = '/home/user/Compass/static/data/pending.json'
CARD_ID = 'g420352ff'


def main(write=False):
    data = json.load(open(PENDING, encoding='utf-8'))
    card = next(c for c in data['cards'] if c['id'] == CARD_ID)
    assert not card.get('pending_since'), card.get('pending_since')
    stamp = datetime.now(timezone.utc).isoformat()

    print('ПРОСТАВЛЯЕМ %s: pending_since = %s' % (CARD_ID, stamp))
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh = json.load(open(PENDING, encoding='utf-8'))
    fresh_card = next(c for c in fresh['cards'] if c['id'] == CARD_ID)
    if fresh_card.get('pending_since'):
        print('кто-то уже поправил — перечитайте')
        return 1
    fresh_card['pending_since'] = stamp
    json.dump(fresh, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
