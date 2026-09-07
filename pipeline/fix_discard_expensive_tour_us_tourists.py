# -*- coding: utf-8 -*-
"""Приток 7 сентября 2026 (14:22) — карточка gd2549bf4 прошла ворота
ошибочно: заголовок «Самый дорогой тур по Москве и Петербургу купили
граждане США за $15 тыс.» (Деловой Петербург, туристическая заметка) не
про сделку M&A вовсе, но разбор заголовка вычленил «Самый дорогой тур по
Москве и Петербургу» как имя покупателя и «граждане США» как предмет —
бессмысленная пара, прошедшая формальную проверку ворот. Тот же класс
дефекта, что g4246335d (10:20) и gd431b049/g8ccc9185 (11:20).

Запуск: python3 pipeline/fix_discard_expensive_tour_us_tourists.py [--write]
"""
import datetime
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING_PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')
STATE_PATH = os.path.join(ROOT, 'data', 'inbox', 'moderation_state.json')

URL = 'https://www.dp.ru/a/2026/09/07/samij-dorogoj-tur-po-moskve'
CARD_ID = 'gd2549bf4'


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

    print(f'Снята карточка {CARD_ID} (туристическая заметка, ложный разбор заголовка ворота пропустили ошибочно).')

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
