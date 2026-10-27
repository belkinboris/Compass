# -*- coding: utf-8 -*-
"""Решение владельца по g4f594e81 сменилось с «approve» на «discard» (id
решения 994, 10:06:44) ПОСЛЕ того, как approve.py --write уже применил более
раннее «approve» (id 973, 08:54:43) и карточка попала в deals_promoted.json
коммитом cbc7972 — до пуша. Решение человека сильнее уже сделанного: убираем
карточку из базы и помечаем её источник как отброшенный, как сделал бы
approve.py, если бы при фетче decisions уже видел решение 994.

Без --write — сухой прогон (печатает, что будет сделано).
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'static' / 'data' / 'deals_promoted.json'
STATE = ROOT / 'data' / 'inbox' / 'moderation_state.json'
DEAL_ID = 'g4f594e81'


def main(write):
    data = json.loads(DATA.read_text(encoding='utf-8'))
    deals = data['deals']
    match = [d for d in deals if d['id'] == DEAL_ID]
    assert len(match) == 1, 'ожидалась ровно одна карточка %s, нашлось %d' % (DEAL_ID, len(match))
    card = match[0]
    urls = [s[1] for s in (card.get('src') or []) if len(s) > 1 and str(s[1]).startswith('http')]

    print('УБРАТЬ ИЗ БАЗЫ: %s «%s»' % (DEAL_ID, card.get('title')))
    for u in urls:
        print('  ОТБРОСИТЬ URL: %s' % u)

    if not write:
        print('Сухой прогон. Применение — с ключом --write.')
        return 0

    data = json.loads(DATA.read_text(encoding='utf-8'))
    deals = data['deals']
    match = [d for d in deals if d['id'] == DEAL_ID]
    assert len(match) == 1, 'ожидалась ровно одна карточка %s, нашлось %d' % (DEAL_ID, len(match))
    data['deals'] = [d for d in deals if d['id'] != DEAL_ID]
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')

    state = json.loads(STATE.read_text(encoding='utf-8'))
    now = datetime.now(timezone.utc).isoformat(timespec='seconds')
    for u in urls:
        state.setdefault('discarded_urls', {})[u] = {
            'id': DEAL_ID, 'title': card.get('title'), 'at': now}
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('Сделано.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
