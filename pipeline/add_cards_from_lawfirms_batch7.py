# -*- coding: utf-8 -*-
"""Партия 7 @LawFirms: две сделки из объявлений, найденных вторым расширением.

ЗАЧЕМ. Формы «сопроводила приобретение» и «выступает консультантом» правило
не знало. Из шести найденных объявлений две сделки уже были в базе с той же
фирмой, одна не сделка, одна карточка дополнена — и две заводятся здесь.

ПРО «НИАРМЕДИК» ОТДЕЛЬНО. В базе есть карточка «АФК «Система» продаёт 50% в
сети клиник «Ниармедик» и «Доктор рядом»» (июнь 2025) — это ДРУГАЯ сделка:
там продавец АФК «Система», здесь продавцами выступили ООО «Доктор Рядом
Холдинг» (СП основателей и ВЭБ.РФ) и ООО «Доктор Рядом Инвест», а покупатель
— ГК «АВС-медицина». Общее название в кавычках у двух сделок — не признак
дубля (урок про банк «Траст», который совпадал сам с собой).

Запуск:
    python3 pipeline/add_cards_from_lawfirms_batch7.py            # сухой прогон
    python3 pipeline/add_cards_from_lawfirms_batch7.py --write    # записать
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
        'url': 'https://t.me/LawFirms/10404',
        'date': '2026-02-05',
        'title': 'ГК «АВС-медицина» приобрела сеть частных клиник «Ниармедик»',
        'ind': 'Здравоохранение',
        'type': 'M&A',
        'status': 'Закрыта',
        'sum': 'Не раскрыта',
        'asset': 'Сеть частных клиник «Ниармедик»',
        'buyer_name': 'ГК «АВС-медицина»',
        'seller': 'ООО «Доктор Рядом Холдинг» и ООО «Доктор Рядом Инвест»',
        'eco': {
            'sum': 'Не раскрыта',
            'share': 'В результате сделки «АВС-медицина» приобрела контроль в отношении '
                     '14 медицинских клиник в Москве и Обнинске.',
            'rationale': 'Закрытие сделки позволило «АВС-медицине» занять лидирующие позиции по '
                         'темпам роста за последний год на рынке частной медицины Москвы и '
                         'двукратно увеличить размер сети.',
            'context': 'Клиники «Ниармедик» будут работать под брендом «АВС-медицина» в едином '
                       'информационном контуре сети. Продавцом выступили ООО «Доктор Рядом '
                       'Холдинг» — совместное предприятие основателей бизнеса и ВЭБ.РФ — и '
                       'ООО «Доктор Рядом Инвест».',
        },
        'law': {
            'struct': 'Приобретение контроля в отношении 14 медицинских клиник.',
            'adv': [['Юридический консультант покупателя (ГК «АВС-медицина»)', 'Delcredere',
                     'Сопровождение на стороне покупателя; советник корпоративной практики и '
                     'руководитель направления M&A Павел Анненков и команда. '
                     'Источник: https://t.me/LawFirms/10404']],
        },
    },
    {
        'url': 'https://t.me/LawFirms/9256',
        'date': '2025-07-14',
        'title': 'ПАО «МТС-Банк» привлекло около 4 млрд ₽ через дополнительную эмиссию акций',
        'ind': 'Банки',
        'type': 'IPO',
        'status': 'Закрыта',
        'sum': '4 млрд ₽',
        'asset': 'ПАО «МТС-Банк»',
        'eco': {
            'sum': '4 млрд ₽',
            'share': 'Дополнительная эмиссия акций ПАО «МТС-Банк», в рамках которой банк '
                     'привлёк в капитал около 4 млрд ₽.',
            'rationale': 'Размещение — часть стратегии банка по наращиванию капитала и созданию '
                         'базы для масштабирования ключевых направлений деятельности. '
                         'Привлечённые средства банк планирует направить на увеличение '
                         'высокодоходного кредитного портфеля и на реализацию потенциальных '
                         'сделок M&A.',
        },
        'law': {
            'struct': 'Дополнительная эмиссия акций.',
            'adv': [['Юридический консультант эмитента', 'VERBA LEGAL',
                     'Сопровождение дополнительной эмиссии акций. '
                     'Источник: https://t.me/LawFirms/9256']],
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
        print('    %s | %s | %s | %s | %s'
              % (card['date'], card['ind'], card['type'], card['status'],
                 ' + '.join(a[1] for a in card['law']['adv'])))

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
