# -*- coding: utf-8 -*-
"""Приток 11 сентября 2026 (05:20 МСК) — карточка g9ca79821 («Картины из
коллекции экс-владельца отеля «Талион» продали на аукционе») прошла ворота
ошибочно: это продажа картин из личной коллекции обанкротившегося
петербургского бизнесмена Александра Ебралидзе на аукционе РАД (портрет
Сталина за ~100 тыс. рублей и ещё два лота) — распродажа имущества в рамках
личного банкротства физлица, не сделка рынка M&A. Поля карточки при этом
были собраны бессмысленно (`buyer_name` пуст, `seller` — весь заголовок,
`asset` — «на аукционе»), что подтверждает: механический разбор просто не
понял структуру этой новости.

Запуск: python3 pipeline/fix_discard_ebralidze_art_auction.py [--write]
"""
import datetime
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ROOT)
PENDING_PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')
STATE_PATH = os.path.join(ROOT, 'data', 'inbox', 'moderation_state.json')

URL = 'https://www.dp.ru/a/2026/09/10/generalissimus-sssr--pejzazh'
CARD_ID = 'g9ca79821'


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

    print(f'Снята карточка {CARD_ID} — продажа картин из личной коллекции банкрота на аукционе, не сделка M&A.')

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
