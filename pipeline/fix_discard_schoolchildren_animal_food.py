# -*- coding: utf-8 -*-
"""Приток 7 сентября 2026 (16:23) — карточка gbd3ad219 прошла ворота
ошибочно: заголовок «Российские школьники вместо цветов на 1 сентября
купили корм для бездомных животных» (Lenta.ru, благотворительная
заметка) не про сделку M&A вовсе, но разбор заголовка вычленил
«Российские школьники вместо цветов на 1 сентября» как имя покупателя и
«корм для бездомных животных» как предмет — бессмысленная пара,
прошедшая формальную проверку ворот. Тот же класс дефекта, что
g4246335d, gd431b049/g8ccc9185, gd2549bf4.

Запуск: python3 pipeline/fix_discard_schoolchildren_animal_food.py [--write]
"""
import datetime
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING_PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')
STATE_PATH = os.path.join(ROOT, 'data', 'inbox', 'moderation_state.json')

URL = 'https://lenta.ru/news/2026/09/07/rossiyskie-shkolniki-vmesto-tsvetov-na-1-sentyabrya-kupili-korm-dlya-bezdomnyh-zhivotnyh/'
CARD_ID = 'gbd3ad219'


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

    print(f'Снята карточка {CARD_ID} (благотворительная заметка, ложный разбор заголовка ворота пропустили ошибочно).')

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
