# -*- coding: utf-8 -*-
"""Партия 3 разбора @LawFirms: две сделки, которых в базе не было.

ЗАЧЕМ. Посты 28–40 канала. Шесть сделок уже были в базе (пять из них
получили факт отдельным прогоном), две пары оказались дублями и слиты, две
сделки заведены здесь, две отклонены как зарубежные.

ОТКЛОНЕНЫ ПО ГРАНИЦЕ, СОГЛАСОВАННОЙ С ВЛАДЕЛЬЦЕМ: размещение облигаций
Telegram на $1,7 млрд (Skadden) и покупка Versace группой Prada (Skadden,
Wachtell) — российской стороны нет ни у той, ни у другой.

ПРО «ЗАПАДНУЮ ГОЛД МАЙНИНГ» ОТДЕЛЬНО. Именно это объявление год назад
связалось автоматом с карточкой про девелопмент («Жилкапинвест») по трём
общим служебным словам — и стало причиной, по которой обогащение пускает в
базу только сильные совпадения. Здесь оно заводится как самостоятельная
карточка, прочитанная человеком, а не по слабому признаку.

ПОКУПАТЕЛЬ БЕЗ ИМЕНИ. У «Западной Голд Майнинг» покупатель назван «частным
инвестором» — как и в партии 2 у «Новамедики», карточка заводится, потому
что названы предмет, продавец и предмет продажи описан конкретно (13
проектов на золотых месторождениях).

ЧЕГО ЗДЕСЬ НЕТ. У сделки по Selectel продавец в объявлении прямо не назван.
Соблазн вывести его из фразы «Servertech Holding Ltd. сохранил за собой
53,564% акций» есть, но это ровно тот случай, что записан в CLAUDE.md: доля
сократилась — не значит, что её продали именно эта сторона. Поле остаётся
пустым, а сама фраза стоит в «Предмете / доле» как цитата.

Запуск:
    python3 pipeline/add_cards_from_lawfirms_batch3.py            # сухой прогон
    python3 pipeline/add_cards_from_lawfirms_batch3.py --write    # записать
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
        'url': 'https://t.me/LawFirms/8978',
        'date': '2025-05-19',
        'title': 'Selectel: проданы 10% акций структурам Геворка Вермишяна и 4,852% — Андрею Голухову',
        'ind': 'ИТ и интернет',
        'type': 'M&A',
        'status': 'Закрыта',
        'sum': 'Не раскрыта',
        'asset': 'Акции Selectel',
        'buyer_name': 'Инвестиционные структуры Геворка Вермишяна и Андрей Голухов',
        'eco': {
            'sum': 'Не раскрыта',
            'share': 'Продажа 10% акций Selectel в пользу инвестиционной компании, основанной '
                     'экс-главой «Мегафона» Геворком Вермишяном, и 4,852% акций в пользу члена '
                     'совета директоров Selectel Андрея Голухова. В результате сделки '
                     'совокупная доля инвестиционных структур под управлением Вермишяна в '
                     'Selectel составила 34%; Servertech Holding Ltd. сохранил за собой '
                     '53,564% акций.',
        },
        'law': {
            'struct': 'Две сделки по продаже акций Selectel: 10% и 4,852%.',
            'adv': [['Юридический консультант Selectel', 'White Square',
                     'Консультирование Selectel по вопросам продажи 10% и 4,852% акций. '
                     'Источник: https://t.me/LawFirms/8978']],
        },
    },
    {
        'url': 'https://t.me/LawFirms/8961',
        'date': '2025-05-15',
        'title': 'Акционеры МКАО «Западная Голд Майнинг» продали группу золотодобывающих компаний',
        'ind': 'ГМК и добыча',
        'type': 'M&A',
        'status': 'Закрыта',
        'sum': 'Не раскрыта',
        'asset': 'Группа золотодобывающих компаний под МКАО «Западная Голд Майнинг»',
        'seller': 'Акционеры МКАО «Западная Голд Майнинг»',
        'eco': {
            'sum': 'Не раскрыта',
            'share': 'Продажа частному инвестору группы золотодобывающих компаний, работающих '
                     'более 40 лет и разрабатывающих 13 проектов на золотых месторождениях на '
                     'Северо-Востоке России и в Восточной Сибири, включая геологоразведку, '
                     'разработку и добычу.',
        },
        'law': {
            'struct': 'Продажа группы золотодобывающих компаний частному инвестору.',
            'adv': [['Юридический консультант продавцов (акционеров МКАО «Западная Голд Майнинг»)',
                     'BIRCH',
                     'Корпоративный, финансовый и налоговый блоки сделки. Проектом руководили '
                     'старший партнёр Антон Ситников и советник Виталий Колосков '
                     '(корпоративный блок), партнёр Антон Баков (финансовый блок) и партнёр '
                     'Андрей Шпак (налоговый блок). Источник: https://t.me/LawFirms/8961']],
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
        print('    предмет: %s' % card['asset'])
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
