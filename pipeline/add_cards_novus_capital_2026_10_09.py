# -*- coding: utf-8 -*-
"""Три сделки, где Novus Capital — названный финансовый консультант (владелец,
9 октября 2026: «собери эти карточки»).

ЗАЧЕМ. На сайте Novus Capital 57 сделок; в базе была одна («Ясно»). Отобраны
российские сделки с 2022 года (раньше база не собирается), у которых названы
стороны. Факты сделки — из прессы; роль Novus Capital — с сайта фирмы
(novuscapital.ru, раздел «Сделки»), он стоит вторым источником.

ЧЕГО НЕ ПРИДУМЫВАЕМ.
- Ципролет/Леволет: пресса пишет о ПОДПИСАННОМ соглашении (21.02.2022), о
  закрытии — нет; статус «Подписана». Сумма не раскрыта.
- «Русский лён»: продавец в прессе не назван — «не раскрыт»; Novus был на его
  стороне. Сумма не раскрыта.
- Чай УПТ: единственный источник — сайт Novus («акционер продал бизнес
  частному инвестору»). Покупатель и продавец по имени не названы; год —
  2024, без месяца.

Проза — своими словами (docs/sources_legal.md, правило 1). Посты в канал не
идут: сделки не свежие, `telegram_posts[id] = None` (бэклог).

Запуск:
    python3 pipeline/add_cards_novus_capital_2026_10_09.py            # сухой прогон
    python3 pipeline/add_cards_novus_capital_2026_10_09.py --write    # записать
"""
import hashlib
import json
import os
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
NOVUS = ['Novus Capital', 'https://novuscapital.ru/']

EMPTY_ECO = {'sum': '—', 'share': '—', 'val': '—', 'target_fin': '—',
             'fin': '—', 'rationale': '—', 'context': '—', 'finadv': '—'}
EMPTY_LAW = {'struct': '—', 'appr': '—', 'adv': [], 'terms': '—'}

PROFILES = {
    'binnopharm': ('Биннофарм Групп', 'Фармацевтика',
                   'Фармацевтический холдинг АФК «Система»: пять производственных площадок в четырёх регионах России.',
                   ['биннофарм']),
    'melkom': ('ГК «Мелком»', 'Пищепром и напитки',
               'Агропромышленная группа из инвестиционной группы «Русские фонды»: макароны «Мелькомбинат» и «Гальяни», '
               'корма для рыбы, аквакультура.',
               ['мелком']),
    'russianlinen': ('«Русский лён»', 'Агро',
                     'Льноперерабатывающий комплекс в Смоленской области: переработка льноволокна, котонизация, '
                     'собственные посевные земли.',
                     ['русский лён', 'русский лен']),
    'upt': ('«Универсальные пищевые технологии»', 'Пищепром и напитки',
            'Производитель чая из Серпухова: марки «Золотая чаша» и KIOKO, контрактное производство чая для других брендов.',
            ['универсальные пищевые технологии']),
}

CARDS = [
    {
        'key': 'novus-binnopharm-ciprolet',
        'date': '2022-02-21',
        'title': '«Биннофарм Групп» покупает у Dr. Reddy\'s права на антибиотики Ципролет и Леволет',
        'ind': 'Фармацевтика', 'type': 'M&A', 'status': 'Подписана', 'sum': 'Не раскрыта',
        'buyer': 'binnopharm', 'seller_id': 'gf80101aa',
        'asset': 'права на препараты Ципролет и Леволет в России, Беларуси и Узбекистане',
        'eco': {
            'sum': 'Не раскрыта',
            'share': 'Права на два антибактериальных бренда — Ципролет и Леволет — для России, Беларуси и Узбекистана.',
            'rationale': 'Покупка укрепляет позиции «Биннофарм Групп» на рынке антибиотиков — одном из ключевых '
                         'для холдинга, — и даёт выход с Ципролетом в Беларусь и Узбекистан.',
            'context': 'Портфель включает таблетки, растворы для инфузий и глазные капли. Производство после '
                       'сделки планируют перенести на площадки «Биннофарм Групп»; на переходный период препараты '
                       'продолжит выпускать Dr. Reddy\'s.',
            'finadv': 'Novus Capital — финансовый консультант продавца (Dr. Reddy\'s)',
        },
        'law': {'struct': 'Права на бренды покупает дочерняя компания холдинга — АО «Алиум». '
                          'Стороны подписали соглашение 21 февраля 2022 года.'},
        'src': [['Ведомости', 'https://www.vedomosti.ru/business/articles/2022/02/21/910278-binnofarm-grupp-vikupaet-prava-na-antibakterialnie-preparati-u-indiiskoi-drreddys'],
                ['ФармМедПром', 'https://pharmmedprom.ru/news/binnofarm-grupp-priobrela-u-dr-reddys-prava-na-dva-antibiotika/'],
                NOVUS],
    },
    {
        'key': 'novus-melkom-russian-linen',
        'date': '2022-07-08',
        'title': 'ГК «Мелком» купила льноперерабатывающий комплекс «Русский лён» в Смоленской области',
        'ind': 'Агро', 'type': 'M&A', 'status': 'Закрыта', 'sum': 'Не раскрыта',
        'buyer': 'melkom', 'target': 'russianlinen',
        'eco': {
            'sum': 'Не раскрыта',
            'share': 'Смоленский льноперерабатывающий комплекс «Русский лён» целиком.',
            'rationale': 'Покупатель рассчитывает на развитие льняной отрасли в России и на синергию: '
                         'выращивание и переработку льна в Смоленской области теперь объединяет одна группа.',
            'context': 'В комплекс входят цех первичной переработки льноволокна, цех котонизации волокна и '
                       'около 8 тыс. га сельскохозяйственной земли. «Мелком» входит в инвестиционную группу '
                       '«Русские фонды».',
            'finadv': 'Novus Capital — финансовый консультант продавца',
        },
        'law': {},
        'src': [['Агроинвестор', 'https://www.agroinvestor.ru/investments/news/38451-gk-melkom-kupila-kompleks-russkiy-len/'],
                NOVUS],
    },
    {
        'key': 'novus-upt-tea',
        'date': '2024',
        'title': 'Акционер продал производителя чая «Универсальные пищевые технологии» частному инвестору',
        'ind': 'Пищепром и напитки', 'type': 'M&A', 'status': 'Закрыта', 'sum': 'Не раскрыта',
        'target': 'upt',
        'eco': {
            'sum': 'Не раскрыта',
            'share': 'Бизнес производителя чая «Универсальные пищевые технологии».',
            'context': 'Компания — один из крупных контрактных производителей чая в России. Имя покупателя '
                       'и условия сделки не раскрывались; о сделке известно из списка проектов её консультанта.',
            'finadv': 'Novus Capital — финансовый консультант продавца',
        },
        'law': {},
        'src': [NOVUS],
    },
]


def pid(key):
    return 'g' + hashlib.md5(('profile:' + key).encode('utf-8')).hexdigest()[:8]


def cid(key):
    return 'g' + hashlib.md5(('card:' + key).encode('utf-8')).hexdigest()[:8]


def build(data):
    comps, ids = data['companies'], {d['id'] for d in data['deals']}
    names = {v.get('name', '').lower().strip('«»"') for v in comps.values()}
    new_profiles = {}
    for key, (name, ind, desc, aliases) in PROFILES.items():
        i = pid(key)
        if i in comps:
            continue
        assert name.lower().strip('«»"') not in names, 'профиль с именем %s уже есть' % name
        new_profiles[i] = ({'name': name, 'ind': ind, 'desc': desc, 'kpi': ['Профиль', 'Автоматический']}, aliases)
    cards = []
    for row in CARDS:
        i = cid(row['key'])
        if i in ids:
            continue
        card = {'id': i, 'date': row['date'], 'title': row['title'], 'ind': row['ind'], 'type': row['type'],
                'status': row['status'], 'sum': row['sum'],
                'eco': dict(EMPTY_ECO, **row['eco']), 'law': dict(EMPTY_LAW, **row['law']),
                'src': [list(s) for s in row['src']], 'added': date.today().isoformat(),
                'from_ingest': True, 'duplicate_reviewed': True}
        for k in ('buyer', 'target'):
            if row.get(k):
                card[k] = pid(row[k])
        if row.get('seller_id'):
            card['seller_id'] = row['seller_id']
        if row.get('asset'):
            card['asset'] = row['asset']
        cards.append(card)
    return new_profiles, cards


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    profiles, cards = build(data)
    for i, (p, a) in profiles.items():
        print('профиль %s  %s' % (i, p['name']))
    for c in cards:
        print('карточка %s  %s | %s | %s' % (c['id'], c['date'], c['status'], c['title']))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    data = json.load(open(DATA, encoding='utf-8'))         # перечитать перед записью
    profiles, cards = build(data)
    for i, (p, aliases) in profiles.items():
        data['companies'][i] = p
        data['match_keys'][i] = aliases
    data['deals'].extend(cards)
    for c in cards:
        data.setdefault('telegram_posts', {})[c['id']] = None
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('Записано: профилей %d, карточек %d' % (len(profiles), len(cards)))
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
