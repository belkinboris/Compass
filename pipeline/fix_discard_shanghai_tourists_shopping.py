# -*- coding: utf-8 -*-
"""Приток 6 сентября 2026 (10:20) — карточка g4246335d прошла ворота
ошибочно: заголовок «Стало известно, что покупают российские туристы в
Шанхае» (ТАСС, обзор потребительских привычек туристов) не про сделку
M&A вовсе, но разбор заголовка вычленил «Стало известно, что» как имя
покупателя и «российские туристы в Шанхае» как предмет — бессмысленная
пара, прошедшая формальную проверку ворот («есть покупатель, есть
предмет»). Это не отказ ворот (raw_screen сюда не относится — карточка
уже была построена и попала в pending.json), поэтому снимается тем же
приёмом (discarded_urls), но до отправки в консоль: карточка удаляется
из pending.json, а адрес источника помечается отклонённым, чтобы не
собраться заново на следующем часовом прогоне.

Запуск: python3 pipeline/fix_discard_shanghai_tourists_shopping.py [--write]
"""
import datetime
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING_PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')
STATE_PATH = os.path.join(ROOT, 'data', 'inbox', 'moderation_state.json')

URL = 'https://tass.ru/ekonomika/28084339'
CARD_ID = 'g4246335d'


def main(write=False):
    with open(PENDING_PATH, encoding='utf-8') as f:
        pending = json.load(f)
    with open(STATE_PATH, encoding='utf-8') as f:
        state = json.load(f)

    matches = [c for c in pending['cards'] if c['id'] == CARD_ID]
    assert len(matches) == 1, f'ожидалась ровно одна карточка {CARD_ID}, найдено {len(matches)}'
    card = matches[0]
    assert any(len(s) > 1 and s[1] == URL for s in (card.get('src') or []))
    assert URL not in state.get('discarded_urls', {})

    pending['cards'] = [c for c in pending['cards'] if c['id'] != CARD_ID]
    state.setdefault('discarded_urls', {})[URL] = {
        'id': CARD_ID, 'title': card.get('title'),
        'at': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
    }

    print(f'Снята карточка {CARD_ID} (обзор покупок туристов, ложный разбор заголовка ворота пропустили ошибочно).')

    if write:
        with open(PENDING_PATH, 'w', encoding='utf-8') as f:
            json.dump(pending, f, ensure_ascii=False, indent=1)
            f.write('\n')
        with open(STATE_PATH, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Записано.')
    else:
        print('(сухой прогон, для записи — --write)')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
