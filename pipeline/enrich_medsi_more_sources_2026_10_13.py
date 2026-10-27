# -*- coding: utf-8 -*-
"""Карточка `g4d7b2e19` (Альфа-Банк/«Медси») — два новых пересказа того же
дня (Frank Media, Rusbase) не дают новых фактов сверх уже записанного,
только новые адреса подтверждения того же события. `enrich.py` их тоже
нашел, но в тот же батч попали риск-строки по другим карточкам (уже
закрытым gddb34475/g3504df38, повторно репостящим тот же факт) — batch
`--write` их тоже применил бы, поэтому добавлено вручную, только `src`.

Источники: Frank Media https://frankmedia.ru/309714,
Rusbase https://rb.ru/news/alfa-bank-kupil-dolyu-v-seti-klinik-medsi-kompaniya-gotovitsya-k-vozmozhnomu-ipo/

Запуск:
    python3 enrich_medsi_more_sources_2026_10_13.py            # сухой прогон
    python3 enrich_medsi_more_sources_2026_10_13.py --write    # применить
"""
import json
import sys

DATA = '/home/user/Compass/static/data/deals_promoted.json'
CARD_ID = 'g4d7b2e19'
NEW_SRCS = [
    ('Frank Media', 'https://frankmedia.ru/309714'),
    ('Rusbase', 'https://rb.ru/news/alfa-bank-kupil-dolyu-v-seti-klinik-medsi-kompaniya-gotovitsya-k-vozmozhnomu-ipo/'),
]


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    card = by_id[CARD_ID]
    existing = {s[1] for s in card.get('src', []) if len(s) > 1}
    to_add = [(n, u) for n, u in NEW_SRCS if u not in existing]

    if not to_add:
        print('Уже применено.')
        return 0
    print('ПРАВКА %s: +src %s' % (CARD_ID, [u for _, u in to_add]))
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    for n, u in to_add:
        card['src'].append([n, u])

    fresh = json.load(open(DATA, encoding='utf-8'))
    fresh_by_id = {d['id']: d for d in fresh['deals']}
    fresh_card = fresh_by_id[CARD_ID]
    fresh_existing = {s[1] for s in fresh_card.get('src', []) if len(s) > 1}
    assert not any(u in fresh_existing for _, u in to_add), 'карточку кто-то уже поправил — перечитайте'
    idx = fresh['deals'].index(fresh_card)
    fresh['deals'][idx] = card
    json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
