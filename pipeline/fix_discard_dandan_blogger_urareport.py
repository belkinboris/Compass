# -*- coding: utf-8 -*-
"""Почасовой приток 4 сентября 2026 (~17:20) — та же ложная карточка о
розничной выручке стрима блогера Даньдань на ВЭФ (не сделка M&A) прошла
ворота ТРЕТИЙ раз за день, на этот раз с URA.RU (`ura.news/news/1053124440`,
seller="Китайский блогер Даньдань за время ВЭФ") — прилагательное перед
«блогер» не поймано правкой `PERSON_ROLE` в draft.py (та правка ловит
только «блогер [из ...]», без ведущего прилагательного). Снимается тем же
способом, что и первые два раза: удаление из pending.json + запись адреса
в moderation_state.json['discarded_urls'], чтобы promote.py не разобрал
его снова под новым id.

Запуск: python3 pipeline/fix_discard_dandan_blogger_urareport.py [--write]
"""
import datetime
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING_PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')
STATE_PATH = os.path.join(ROOT, 'data', 'inbox', 'moderation_state.json')

URL = 'https://ura.news/news/1053124440'
CARD_ID = 'gf440dc1c'


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

    print(f'Снята карточка {CARD_ID}, адрес {URL} записан в discarded_urls.')

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
