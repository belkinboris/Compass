# -*- coding: utf-8 -*-
"""Карточка gd09e0945 («Леста Игры» / АО «Промышленные сооружения»):
единственным источником была недоступная напрямую Frank Media, а её
автособранная заметка о событии несла необработанный HTML (`&#171;`) и
служебный RSS-хвост («Сообщение … появилось сначала на Frank Media») —
не текст для читателя. Добавляет источники, найденные исследованием
(Коммерсантъ, Ведомости — два самых подробных), переписывает заметку
события и поправляет `party_evidence`, который после fix_lesta_parties
остался со старыми (перепутанными) значениями полей.

Запуск:
    python3 pipeline/fix_lesta_sources_event_2026_10_16.py            # сухой прогон
    python3 pipeline/fix_lesta_sources_event_2026_10_16.py --write    # применить
"""
import json
import sys

PENDING = '/home/user/Compass/static/data/pending.json'
CARD_ID = 'gd09e0945'

KOMMERSANT = ['Коммерсантъ', 'https://www.kommersant.ru/doc/9027870']
VEDOMOSTI = ['Ведомости', 'https://www.vedomosti.ru/media/articles/2026/10/16/1237602-vladeltsem-gk-lesta']

NEW_NOTE = ('Группа «Леста Игры» перешла в собственность Росимущества летом 2025 года '
            'после решения суда о национализации; покупатель получил три юрлица группы, '
            'переход уже отражён в ЕГРЮЛ.')


def main(write=False):
    data = json.load(open(PENDING, encoding='utf-8'))
    cards = {c['id']: c for c in data['cards']}
    card = cards[CARD_ID]
    urls = {s[1] for s in card['src']}
    for a in (KOMMERSANT, VEDOMOSTI):
        assert a[1] not in urls, 'источник уже стоит: %r' % a
    assert card['events'][0]['note'].startswith('С 2025 года'), 'заметка события уже не та — перечитайте'
    assert card['party_evidence']['buyer'][0]['value'] == 'Игровую студию «Леста»', 'party_evidence уже поправлен'
    print('src += Коммерсантъ, Ведомости')
    print('events[0].note переписывается (снят необработанный HTML и RSS-хвост)')
    print('party_evidence поправляется на текущие значения полей')
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh = json.load(open(PENDING, encoding='utf-8'))
    fc = {c['id']: c for c in fresh['cards']}[CARD_ID]
    fresh_urls = {s[1] for s in fc['src']}
    for a in (KOMMERSANT, VEDOMOSTI):
        assert a[1] not in fresh_urls, 'источник поменяли параллельно — перечитайте'
        fc['src'].append(a)
    assert fc['events'][0]['note'].startswith('С 2025 года'), 'заметка поменялась параллельно — перечитайте'
    fc['events'][0]['note'] = NEW_NOTE
    fc['events'][0]['source'] = KOMMERSANT
    fc['party_evidence'] = {
        'buyer': [{'value': fc['buyer_name'], 'field': 'buyer_name',
                   'method': 'research', 'url': KOMMERSANT[1]}],
        'target': [{'value': fc['asset'], 'field': 'asset',
                    'method': 'research', 'url': KOMMERSANT[1]}],
        'seller': [{'value': fc['seller'], 'field': 'seller',
                    'method': 'research', 'url': VEDOMOSTI[1]}],
    }
    json.dump(fresh, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
