# -*- coding: utf-8 -*-
"""Партия 4 разбора @LawFirms: три сделки, которых в базе не было.

ЗАЧЕМ. Посты 41–55 канала. Восемь сделок уже были в базе с полными
консультантами, три карточки получили факты (`enrich_from_lawfirms_batch4.py`),
две записи отклонены, три сделки заведены здесь.

СП С ИРАНОМ — ЭТО НЕ «ЗАРУБЕЖНАЯ СДЕЛКА». Граница, о которой договорились
с владельцем, отсекает объявления БЕЗ российской стороны (IPO Space X,
Prada/Versace). Здесь российская сторона — «Центр развития НОВО», и то, что
инфраструктура строится в Иране, сделку из базы не выводит: это российский
участник и российский юридический консультант.

ТИП «СОЗДАНИЕ СП» — не выдумка этого прогона, а уже существующее в базе
значение (`selectel-itmo`). Совместное предприятие — не покупка готового
бизнеса, и записывать его как M&A значило бы поставить в плашку сторон
покупателя и продавца, которых нет.

Запуск:
    python3 pipeline/add_cards_from_lawfirms_batch4.py            # сухой прогон
    python3 pipeline/add_cards_from_lawfirms_batch4.py --write    # записать
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
        'url': 'https://t.me/LawFirms/8290',
        'date': '2024-12-26',
        'title': '«Р-Фарм» приобрела 49,9% в группе «Центр ЭКО»',
        'ind': 'Здравоохранение',
        'type': 'M&A',
        'status': 'Закрыта',
        'sum': 'Не раскрыта',
        'asset': 'Группа «Центр ЭКО»',
        'buyer_name': '«Р-Фарм»',
        'eco': {
            'sum': 'Не раскрыта',
            'share': 'Приобретение 49,9% в группе «Центр ЭКО», объединяющей 29 операционных '
                     'компаний.',
            'context': '«Центр ЭКО» входит в тройку крупнейших игроков в сегменте '
                       'вспомогательных репродуктивных технологий (ВРТ) в России и управляет '
                       '35 клиниками репродуктивного здоровья.',
        },
        'law': {
            'struct': 'Приобретение 49,9% в группе «Центр ЭКО».',
            'adv': [['Юридический консультант покупателя («Р-Фарм»)', 'Better Chance',
                     'Партнёр корпоративной практики Артём Тамаев, старший юрист Андрей Шевчук '
                     'и команда юристов. Источник: https://t.me/LawFirms/8290']],
        },
    },
    {
        'url': 'https://t.me/LawFirms/8286',
        'date': '2024-12-25',
        'title': 'Selectel приобрёл облачного провайдера «Единая сеть» (Servers.ru)',
        'ind': 'ИТ и интернет',
        'type': 'M&A',
        'status': 'Закрыта',
        'sum': 'Не раскрыта',
        'asset': 'Компания «Единая сеть» (бренды Servers.ru, Exepto.ru, Fozzy.ru)',
        'buyer_name': 'Selectel',
        'eco': {
            'sum': 'Не раскрыта',
            'share': 'Приобретение компании «Единая сеть», работающей под брендами Servers.ru, '
                     'Exepto.ru и Fozzy.ru.',
            'rationale': 'Сделка направлена на ускорение роста бизнеса и укрепление позиций '
                         'Selectel в сегменте облачных инфраструктурных сервисов.',
            'context': '«Единая сеть» в 2023 году занимала третье место среди провайдеров услуг '
                       'аренды выделенных серверов с долей рынка 10%.',
        },
        'law': {
            'struct': 'Приобретение компании «Единая сеть».',
            'adv': [['Юридический консультант покупателя (Selectel)', 'White Square',
                     'Партнёр Елизавета Ракова, советник Валерий Лавров, юрист Григор Восканян, '
                     'помощник юриста Данил Бессонов. Источник: https://t.me/LawFirms/8286']],
        },
    },
    {
        'url': 'https://t.me/LawFirms/8126',
        'date': '2024-11-19',
        'title': '«Центр развития НОВО» и IranianEurasia создают СП для зернового хаба в Иране',
        'ind': 'Агро',
        'type': 'Создание СП',
        'status': 'Подписана',
        'sum': 'Не раскрыта',
        'asset': 'Совместное предприятие «Центра развития НОВО» и IranianEurasia Trading and Logistics',
        'eco': {
            'sum': 'Не раскрыта',
            'share': 'Учредители совместного предприятия — «Центр развития НОВО» и иранская '
                     'логистическая компания IranianEurasia Trading and Logistics; доли не '
                     'раскрыты.',
            'rationale': 'Соглашение предусматривает строительство зернового хаба в рамках '
                         'программы «Зерно +».',
            'context': 'Совместное предприятие и инфраструктура разместятся в особой '
                       'экономической зоне Серахс на северо-востоке Ирана — на ключевом '
                       'транзитном маршруте между Центральной Азией и Ближним Востоком, '
                       'в рамках международного транспортного коридора «Север — Юг».',
        },
        'law': {
            'struct': 'Создание совместного предприятия двух учредителей.',
            'adv': [['Юридический консультант проекта', 'VERBA LEGAL',
                     'Полное сопровождение проекта, включая разработку корпоративной '
                     'документации. Источник: https://t.me/LawFirms/8126']],
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
        print('    предмет: %s' % card['asset'][:70])
        print('    стороны: покупатель=%s продавец=%s'
              % (card.get('buyer') or card.get('buyer_name') or '—', card.get('seller') or '—'))
        print('    консультант: %s' % ' + '.join(a[1] for a in card['law']['adv']))

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
