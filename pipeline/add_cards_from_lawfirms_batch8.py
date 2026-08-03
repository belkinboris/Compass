# -*- coding: utf-8 -*-
"""Партия 8 @LawFirms: сделка из новости канала, а не из объявления фирмы.

ЗАЧЕМ. Хвост потока — новости о сделках без имени юрфирмы. Почти все они уже
в базе; эта — нет.

КОНСУЛЬТАНТА ЗДЕСЬ НЕТ И НЕ БУДЕТ ПРИДУМАН. Пост прямо заканчивается
вопросом «Интересно, использовали ли стороны внешних юридических
консультантов для сопровождения сделки?» — то есть канал сам не знает.
Поле остаётся пустым.

Запуск:
    python3 pipeline/add_cards_from_lawfirms_batch8.py            # сухой прогон
    python3 pipeline/add_cards_from_lawfirms_batch8.py --write    # записать
"""
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

SRC_LABEL = 'РУЛЬФЫ, ИЛЬФЫ И ИНХАУСЫ (@LawFirms)'

EMPTY_ECO = {'sum': '—', 'share': '—', 'val': '—', 'target_fin': '—',
             'fin': '—', 'rationale': '—', 'context': '—', 'finadv': '—'}
EMPTY_LAW = {'struct': '—', 'appr': '—', 'adv': [], 'terms': '—'}

CARDS = [
    {
        'url': 'https://t.me/LawFirms/11169',
        'date': '2026-07-16',
        'title': 'VK договорилась о продаже 100% магазина приложений RuStore Дмитрию Панкрушеву',
        'ind': 'ИТ и интернет',
        'type': 'M&A',
        # «Договорилась о продаже» — это подписание, а не закрытие.
        'status': 'Подписана',
        'sum': 'Не раскрыта',
        'asset': 'Магазин приложений RuStore',
        'buyer_name': 'Дмитрий Панкрушев',
        'seller': 'VK',
        'eco': {
            'sum': 'Не раскрыта',
            'share': 'Все 100% акций магазина приложений RuStore будут проданы генеральному '
                     'директору компании-разработчика Дмитрию Панкрушеву.',
            'context': 'Дмитрий Панкрушев возглавляет ООО «Много приложений» — компанию, '
                       'которую VK привлекал к разработке RuStore.',
        },
        'law': {
            'struct': 'Продажа 100% акций.',
            # Канал прямо пишет, что не знает, привлекались ли консультанты.
            'adv': [['Стороны сделки', 'Не раскрывались',
                     'Юридические консультанты в публичных источниках не раскрывались']],
        },
    },
]


def card_id(url, existing):
    """id выводится из адреса объявления: повторный прогон даст тот же id."""
    candidate = 'g' + hashlib.md5(url.encode('utf-8')).hexdigest()[:8]
    assert candidate not in existing, 'id %s занят — карточка уже заведена?' % candidate
    return candidate


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    ids = {d['id'] for d in data['deals']}
    urls = {str(s[1]) for d in data['deals'] for s in (d.get('src') or []) if len(s) > 1}
    titles = {str(d.get('title') or '').lower() for d in data['deals']}

    built = []
    for row in CARDS:
        assert row['url'] not in urls, '%s уже стоит источником у какой-то карточки' % row['url']
        assert row['title'].lower() not in titles, 'карточка с таким заголовком уже есть'
        card = {
            'id': card_id(row['url'], ids),
            'date': row['date'],
            'title': row['title'],
            'ind': row['ind'],
            'type': row['type'],
            'status': row['status'],
            'sum': row['sum'],
            'asset': row['asset'],
            'eco': dict(EMPTY_ECO, **row['eco']),
            'law': dict(EMPTY_LAW, **row['law']),
            'src': [[SRC_LABEL, row['url']]],
            'from_ingest': True,
            'duplicate_reviewed': True,
        }
        for key in ('buyer', 'buyer_name', 'seller'):
            if row.get(key):
                card[key] = row[key]
        assert not (card.get('buyer') and card.get('buyer_name')), \
            'у покупателя нельзя заполнять и профиль, и имя текстом'
        ids.add(card['id'])
        built.append(card)

    for card in built:
        print('%s  %s' % (card['id'], card['title'][:70]))
        print('    %s | %s | %s | %s' % (card['date'], card['ind'], card['type'], card['status']))
        print('    продавец=%s покупатель=%s' % (card.get('seller'), card.get('buyer_name')))

    print('\nновых карточек: %d' % len(built))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0

    data['deals'].extend(built)
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО в %s' % os.path.relpath(DATA, ROOT))
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
