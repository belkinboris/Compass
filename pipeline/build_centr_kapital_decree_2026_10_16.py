# -*- coding: utf-8 -*-
"""Новые карточки: указ президента (вносит изменения в указ №302 от
25 апреля 2023) передал во временное управление ООО «УК "Центр
Капитал"» активы пяти компаний — производителя напольных покрытий
Tarkett и четырёх упаковочных компаний (Каппа Рус, Менсен Пакаджинг
СНГ, Онтэкс РУ — владелец бренда Helen Harper, Эвиосис Пэкэджинг
Кубань). Тот же механизм, что уже решался для Nestlé/«Ашана»/FM
Logistic/«Леманы ПРО» (17 сентября) и Metro (28 сентября) — по карточке
на компанию, управляющий — один и тот же для всех пяти.

Источники (несколько изданий, перекрёстно): Ведомости, Lenta.ru,
ВЗГЛЯД, URA.RU, RuNews24.ru, Вести.ru, Mail.ru. Точный номер и дата
самого указа (в отличие от указа №302, который он меняет) не названы
ни в одном найденном источнике — только публикация на pravo.gov.ru
(id 0001202610150039, ~15 октября), которую не удалось открыть из этой
песочницы.

Запуск:
    python3 pipeline/build_centr_kapital_decree_2026_10_16.py            # сухой прогон
    python3 pipeline/build_centr_kapital_decree_2026_10_16.py --write    # применить
"""
import json
import os
import sys
from datetime import datetime, timezone

ROOT = '/home/user/Compass'
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import promote  # noqa: E402

PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

SRC_VEDOMOSTI = ['Ведомости', 'https://www.vedomosti.ru/business/news/2026/10/16/1237536-aktivi-tarkett']
SRC_VZGLYAD = ['ВЗГЛЯД', 'https://vz.ru/news/2026/10/16/1463559.html']
SRC_LENTA = ['Lenta.ru', 'https://lenta.ru/news/2026/10/16/tarkett/']
SRC_URA = ['URA.RU', 'https://ura.news/news/1053136498']
SRC_RUNEWS24 = ['RuNews24.ru',
                'https://runews24.ru/politics/16/10/2026/putin-podpisal-ukaz-4-upakovochnyie-kompanii-ushli-pod-upravlenie-czentr-kapital']
SRC_VESTI = ['Вести.ru',
             'https://www.vesti.ru/ns/putin-peredal-vo-vremennoe-upravlenie-aktivy-kompanij-s-vyruchkoj-bolee-rub50-mlrd']
SRC_MAIL = ['Mail.ru', 'https://news.mail.ru/economics/72740261/']

EVENT_NOTE = 'Президент передал активы во временное управление ООО «УК "Центр Капитал"».'

CARDS = [
    {
        'title': 'Активы Tarkett в России переданы во временное управление «Центр Капиталу»',
        'ind': 'Строительство',
        'seller': 'Tarkett',
        'asset': 'российские активы производителя напольных покрытий Tarkett (АО «Таркетт», АО «Таркетт Рус», ООО «Таркетт Соммер»)',
        'src': [SRC_VEDOMOSTI, SRC_VZGLYAD, SRC_LENTA],
    },
    {
        'title': 'Активы «Каппа Рус» переданы во временное управление «Центр Капиталу»',
        'ind': 'Производство тары',
        'seller': None,
        'asset': 'российские активы производителя упаковки «Каппа Рус»',
        'src': [SRC_URA, SRC_RUNEWS24],
    },
    {
        'title': 'Активы «Менсен Пакаджинг СНГ» переданы во временное управление «Центр Капиталу»',
        'ind': 'Производство тары',
        'seller': None,
        'asset': 'российские активы производителя упаковки «Менсен Пакаджинг СНГ»',
        'src': [SRC_URA, SRC_RUNEWS24],
    },
    {
        'title': 'Активы «Онтэкс РУ» (бренд Helen Harper) переданы во временное управление «Центр Капиталу»',
        'ind': 'Потребительские товары',
        'seller': 'Ontex Group',
        'asset': 'российские активы «Онтэкс РУ» — владельца бренда Helen Harper',
        'src': [SRC_URA, SRC_MAIL, SRC_RUNEWS24],
    },
    {
        'title': 'Активы «Эвиосис Пэкэджинг Кубань» переданы во временное управление «Центр Капиталу»',
        'ind': 'Производство тары',
        'seller': None,
        'asset': 'российские активы производителя упаковки «Эвиосис Пэкэджинг Кубань»',
        'src': [SRC_URA, SRC_RUNEWS24],
    },
]


def main(write=False):
    pending = json.load(open(PENDING, encoding='utf-8'))
    promoted = json.load(open(DATA, encoding='utf-8'))
    existing_ids = {c['id'] for c in pending['cards']} | {d['id'] for d in promoted['deals']}
    existing_titles = {c.get('title') for c in pending['cards']}

    new_cards = []
    for spec in CARDS:
        if spec['title'] in existing_titles:
            print('ПРОПУСК: уже в pending.json — %s' % spec['title'])
            continue
        card_id = promote.new_id(existing_ids | {c['id'] for c in new_cards})
        draft = {
            'date': '2026-10-16',
            'title': spec['title'],
            'ind': spec['ind'],
            'type': 'M&A',
            'status': 'Закрыта',
            'src': spec['src'],
            'asset': spec['asset'],
            'events': [{
                'kind': 'closed',
                'date': '2026-10-16',
                'title': 'Указ подписан',
                'note': EVENT_NOTE,
                'source': spec['src'][0],
            }],
        }
        if spec['seller']:
            draft['seller'] = spec['seller']
        card = promote.to_card(draft, card_id)
        card['kind'] = 'custody'
        card['pending_since'] = datetime.now(timezone.utc).isoformat()
        new_cards.append(card)
        print('НОВАЯ КАРТОЧКА %s: %s' % (card_id, card['title']))

    if not write:
        print('\nСухой прогон (%d карточек). Применение — с ключом --write.' % len(new_cards))
        return 0

    fresh = json.load(open(PENDING, encoding='utf-8'))
    fresh_ids = {c['id'] for c in fresh['cards']}
    if any(c['id'] in fresh_ids for c in new_cards):
        print('ОТКАЗ: id уже занят — перечитайте и повторите')
        return 1
    fresh['cards'].extend(new_cards)
    json.dump(fresh, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено: %d карточек.' % len(new_cards))
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
