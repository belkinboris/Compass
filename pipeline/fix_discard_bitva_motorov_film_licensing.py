# -*- coding: utf-8 -*-
"""Приток 9 сентября 2026 (08:20 МСК) — карточка gae255021 («Фильм «Битва
моторов» продали для проката в страны Латинской Америки и Европы») прошла
ворота ошибочно: это лицензирование прав на зарубежный кинопрокат фильма
(продюсер Пётр Ануров про ленту об Андрее Нагеле и Дмитрии Бондареве), а не
сделка рынка M&A — не меняется владелец компании, не продаются доли или
активы. Механический разбор принял глагол «продали» за признак M&A и
записал сам фильм продавцом, а обрывок фразы «для проката в страны Латинской
Америки и Европы» — предметом сделки.

Запуск: python3 pipeline/fix_discard_bitva_motorov_film_licensing.py [--write]
"""
import datetime
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING_PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')
STATE_PATH = os.path.join(ROOT, 'data', 'inbox', 'moderation_state.json')

URL = 'https://tass.ru/kultura/28093541'
CARD_ID = 'gae255021'


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

    print(f'Снята карточка {CARD_ID} — лицензирование кинопроката, не сделка рынка M&A.')

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
