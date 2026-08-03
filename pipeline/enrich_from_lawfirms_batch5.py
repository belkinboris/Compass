# -*- coding: utf-8 -*-
"""Партия 5 разбора @LawFirms: последние 36 объявлений канала (2022–2024).

ЗАЧЕМ. Посты 56–91 — хвост архива. Здесь много сделок, о которых база уже
знает: у одиннадцати карточек консультант стоял и совпал с объявлением
(«Метрополис», Hugo Boss, «Мега»/Ingka, «Европлан», Hygienic,
«Форвард-Маркет», Дом Зингера, Кун-Манье, «Рексофт», «Самолет»/МИЦ,
«Яндекс.Здоровье») — это и есть проверка того, что прошлые волны разбора
сработали. Семь карточек факт получают.

ЧЕТЫРЕ ЗАГЛУШКИ ОПРОВЕРГНУТЫ ИСТОЧНИКОМ: «Элсиб», «Новомет», IPO
«Диасофта» и «Евроонко» стояли с «Стороны сделки — Не раскрывались», а
фирмы объявили о сопровождении публично.

ЧТО ЗДЕСЬ ЕЩЁ ПРАВИТСЯ, КРОМЕ КОНСУЛЬТАНТОВ. Два статуса, и оба — вперёд,
по прямому указанию объявления: X5 Group закрыла покупку «Красного Яра» и
«Слаты» (у карточки статуса не было вовсе), стороны по «Евроонко» подписали
соглашение в начале сентября 2024 года (карточка стояла «Обсуждается»).

ЧТО ОТЛОЖЕНО. Объявление АЛРУД о покупке контрольного пакета ПАО «Калужский
турбинный завод» называет предмет и ни одной стороны. Объявление BGP
Litigation о «двух сделках фонда «Восход»» не называет ни предмета, ни
сторон («компания в сфере разработки сложных месторождений нефти»),
и связать его с карточками фонда в базе нечем.

ЧТО ПРОПУЩЕНО ПО ГРАНИЦЕ. IPO Trump Media (Truth Social), IPO Air Astana и
IPO Международного аэропорта Афин — российской стороны нет. Три поста
канала оказались не объявлениями, а просьбами к подписчикам назвать
юристов; правило `advisors.lead_advisor` приняло начало фразы («Если кто
знает, какие юридические фирмы…») за название фирмы.

Запуск:
    python3 pipeline/enrich_from_lawfirms_batch5.py            # сухой прогон
    python3 pipeline/enrich_from_lawfirms_batch5.py --write    # записать
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

SRC_LABEL = 'РУЛЬФЫ, ИЛЬФЫ И ИНХАУСЫ (@LawFirms)'

EMPTY_ECO = {'sum': '—', 'share': '—', 'val': '—', 'target_fin': '—',
             'fin': '—', 'rationale': '—', 'context': '—', 'finadv': '—'}

ADVISORS = [
    ('g6520943f',
     'Юридический консультант продавца (UNIQA)',
     'АЛРУД',
     'Комплексная юридическая поддержка UNIQA в сделке по продаже «Райффайзен Лайф» группе '
     '«Ренессанс Страхование». Источник: https://t.me/LawFirms/7988',
     'https://t.me/LawFirms/7988', None,
     ['Юридический консультант покупателя (Ренессанс страхование)']),
    ('g62f09353',
     'Юридический консультант продавца (АО «Кузбассэнерго»)',
     'ALUMNI Partners',
     'Сопровождение АО «Кузбассэнерго» в сделке по продаже 98,36% акций НПО «Элсиб». '
     'Источник: https://t.me/LawFirms/7765',
     'https://t.me/LawFirms/7765', 'Стороны сделки', ['Стороны сделки']),
    ('gd73fd825',
     'Юридический консультант одного из участников консорциума покупателей',
     'АЛРУД',
     'Сопровождение одного из участников консорциума покупателей российского бизнеса '
     '«Яндекса». Источник: https://t.me/LawFirms/7368',
     'https://t.me/LawFirms/7368', None,
     ['Юридический консультант', 'Юридический консультант', 'Представляла yandex n.v. (продавца)']),
    ('gdb4b1cbf',
     'Юридический консультант продавца («Роснано»)',
     'ALUMNI Partners',
     'Сопровождение «Роснано» в связи с продажей доли участия в «Новомете». '
     'Источник: https://t.me/LawFirms/7143',
     'https://t.me/LawFirms/7143', 'Стороны сделки', ['Стороны сделки']),
    ('g202f49be',
     'Юридический консультант размещения',
     'LECAP',
     'Сопровождение IPO «Диасофта» на Московской бирже. '
     'Источник: https://t.me/LawFirms/6881',
     'https://t.me/LawFirms/6881', 'Стороны сделки', ['Стороны сделки']),
    ('g3b9c077a',
     'Юридический консультант покупателя (АО «Тетра»)',
     'NSP',
     'Структурирование и полное юридическое сопровождение сделки, включая подписание. '
     'По условиям соглашения покупателю передаётся до 99,99% долей участия в компаниях, '
     'контролирующих сеть клиник. Источник: https://t.me/LawFirms/7999',
     'https://t.me/LawFirms/7999', 'Стороны сделки', ['Стороны сделки']),
]

# Тонкая карточка X5/«Красный Яр»: `law.adv` пуст, `eco` нет вовсе, статуса нет.
FILL = [
    {
        'id': 'cf9e8af73',
        'url': 'https://t.me/LawFirms/5067',
        'expect': {'status': None},
        'set': {'status': 'Закрыта'},
        'eco': {
            'share': 'Приобретение 70% долей в бизнесах «Красный Яр» и «Слата» в Восточной '
                     'Сибири.',
        },
        'law': {
            'struct': 'Приобретение 70% долей в бизнесах «Красный Яр» и «Слата».',
            'adv': [['Юридический консультант покупателя (X5 Group)', 'ALUMNI Partners',
                     'Юридическое сопровождение приобретения 70% долей в бизнесах «Красный Яр» '
                     'и «Слата». Источник: https://t.me/LawFirms/5067']],
        },
    },
]

# Статус двигается только вперёд и только по прямому указанию объявления.
STATUS = [
    ('g3b9c077a', 'Обсуждается', 'Подписана',
     'стороны подписали соглашение в начале сентября 2024 года'),
]


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}

    for did, role, firm, note, url, drop, before in ADVISORS:
        deal = by_id.get(did)
        assert deal is not None, 'карточки %s нет в базе' % did
        adv = (deal.get('law') or {}).get('adv') or []
        assert firm.lower() not in ' | '.join(str(a[1]) for a in adv if len(a) > 1).lower(), \
            '%s: %s уже записан' % (did, firm)
        assert [str(a[0]) for a in adv if a] == before, \
            '%s: роли другие (%r)' % (did, [str(a[0]) for a in adv if a])
        assert url not in {str(s[1]) for s in (deal.get('src') or []) if len(s) > 1}, \
            '%s: объявление уже стоит в источниках' % did
        print('%s  %s' % (did, (deal.get('title') or '')[:58]))
        if drop:
            print('    убрать заглушку: %s' % drop)
        print('    + %s — %s' % (role, firm))

    for row in FILL:
        deal = by_id.get(row['id'])
        assert deal is not None, 'карточки %s нет в базе' % row['id']
        for key, value in row['expect'].items():
            assert deal.get(key) == value, '%s: %s сейчас %r' % (row['id'], key, deal.get(key))
        print('%s  %s' % (row['id'], (deal.get('title') or '')[:58]))
        print('    наполняется: %s' % ', '.join(list(row['set']) + list(row.get('eco') or {})
                                                + list(row.get('law') or {})))

    for did, was, now, why in STATUS:
        deal = by_id.get(did)
        assert deal is not None, 'карточки %s нет в базе' % did
        assert deal.get('status') == was, '%s: статус сейчас %r, а не %r' % (
            did, deal.get('status'), was)
        print('%s  статус %s -> %s (%s)' % (did, was, now, why))

    print('\nправок: %d' % (len(ADVISORS) + len(FILL) + len(STATUS)))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0

    for did, role, firm, note, url, drop, before in ADVISORS:
        deal = by_id[did]
        law = deal.setdefault('law', {})
        law['adv'] = [a for a in (law.get('adv') or []) if not (drop and str(a[0]) == drop)]
        law['adv'].append([role, firm, note])
        deal.setdefault('src', []).append([SRC_LABEL, url])
    for row in FILL:
        deal = by_id[row['id']]
        deal.update(row['set'])
        eco = dict(EMPTY_ECO, **(deal.get('eco') or {}))
        eco.update(row.get('eco') or {})
        deal['eco'] = eco
        law = deal.setdefault('law', {})
        for key, value in (row.get('law') or {}).items():
            if key == 'adv':
                law.setdefault('adv', []).extend(value)
            else:
                law[key] = value
        law.setdefault('adv', [])
        for key in ('struct', 'appr', 'terms'):
            law.setdefault(key, '—')
        deal.setdefault('src', []).append([SRC_LABEL, row['url']])
    for did, was, now, why in STATUS:
        by_id[did]['status'] = now

    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО в %s' % os.path.relpath(DATA, ROOT))
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
