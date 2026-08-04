# -*- coding: utf-8 -*-
"""Партия 4 разбора @LawFirms: три карточки, две из них — «мало данных».

ЗАЧЕМ. Посты 41–55 канала. Восемь сделок уже были в базе с полными
консультантами — и это хорошо, значит прошлые волны разбора сработали. Но
две карточки, у которых на экране стоит блок «мало данных», объявление
наполняет фактами целиком, а не одним именем фирмы. Ровно тот случай,
о котором говорил владелец: дубль есть, а информации в нём нет.

САМАЯ ЦЕННАЯ ПРАВКА — SELGROS. Карточка называлась «Selgros ищет покупателя
для российского бизнеса (переговоры на стадии поиска)» и стояла так с ноября
2024 года. Сделка давно закрыта: австрийский акционер MCCR Beteiligungs GmbH
продал 100% доли в группе «Зельгрос Россия» компании «Ароса-Логистика».
Заголовок в настоящем времени про поиск покупателя — это не пустое поле, а
устаревшее утверждение, и читателю оно врёт сильнее пустоты. Поэтому здесь
меняется и заголовок, и статус — ровно то, что делает `enrich.py` при новой
стадии, только руками и с проверкой исходного значения.

ЧТО НАМЕРЕННО НЕ ЗАПИСАНО. Объявление Orion про «Бери Заряд!» называет
750 млн ₽ — это pre-IPO раунд мая, а не цена покупки «Яндексом». Разбор
предлагал её как сумму сделки; тот же класс ошибки, что «ВТБ продал
Holiday Inn».

ЧТО ОТЛОЖЕНО. Объявление ККМП о покупке контролирующего пакета АО «ПРОГРЕСС»
(«ФрутоНяня») называет предмет, но НИ ОДНОЙ стороны: «представляла интересы
покупателя» — и всё. Пост канала с вопросом «кто сопровождает переговоры
«М.Видео-Эльдорадо» и Промсвязьбанка» — вообще не объявление о сделке, а
просьба к подписчикам; правило `advisors.lead_advisor` приняло начало фразы
за название фирмы.

Запуск:
    python3 pipeline/enrich_from_lawfirms_batch4.py            # сухой прогон
    python3 pipeline/enrich_from_lawfirms_batch4.py --write    # записать
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
    ('g4feb42fc',
     'Юридический консультант продавца (F.A.C.C.T.)',
     'Никольская Консалтинг',
     'Сопровождение F.A.C.C.T. на всех этапах структурирования и реализации проекта: '
     'транзакционная документация, подписание и закрытие. Сделка предполагала передачу '
     'основных инженерных технологий и переход сотрудников в новую ИБ-компанию. '
     'Источник: https://t.me/LawFirms/8455',
     'https://t.me/LawFirms/8455',
     ['Юридический консультант покупателя (фонд «Сайберус»)']),
]

# Тонкие карточки: пост наполняет их фактами, а не одним именем фирмы.
FILL = [
    {
        'id': 'cbb6ba4c9',
        'url': 'https://t.me/LawFirms/8293',
        'expect': {'status': None, 'sum': None, 'buyer_name': None, 'asset': None},
        'set': {
            'status': 'Закрыта',
            'buyer_name': 'АО «Альфа-Банк»',
            'asset': 'АО «Пушкинский» и ООО «КАРО ФИЛЬМ Севастопольский»',
        },
        'eco': {
            'share': 'Приобретение АО «Пушкинский», в периметр активов которого входит '
                     'кинотеатр «Россия» на Пушкинской площади, и ООО «КАРО ФИЛЬМ '
                     'Севастопольский».',
        },
        'law': {
            'struct': 'Приобретение АО «Пушкинский» и ООО «КАРО ФИЛЬМ Севастопольский».',
        },
    },
    {
        'id': 'cea87de0a',
        'url': 'https://t.me/LawFirms/8221',
        'expect': {'status': None, 'sum': None, 'buyer_name': None, 'asset': None,
                   'title': 'Selgros ищет покупателя для российского бизнеса '
                            '(переговоры на стадии поиска)'},
        'set': {
            'title': 'Selgros продал 100% группы «Зельгрос Россия» компании «Ароса-Логистика»',
            'status': 'Закрыта',
            'seller': 'MCCR Beteiligungs GmbH (австрийский акционер Selgros)',
            'buyer_name': '«Ароса-Логистика»',
            'asset': 'Группа компаний «Зельгрос Россия»',
        },
        'eco': {
            'share': 'Продажа австрийским акционером MCCR Beteiligungs GmbH 100% доли в группе '
                     'компаний «Зельгрос Россия».',
            'context': '«Зельгрос Cash & Carry» и «Глобал Фудс», входящие в группу «Зельгрос '
                       'Россия», продолжат работать под собственными брендами, несмотря на '
                       'смену собственника.',
        },
        'law': {
            'struct': 'Продажа 100% доли в группе компаний «Зельгрос Россия».',
            'adv': [['Юридический консультант', 'Nextons',
                     'Сопровождение сделки; команду возглавляли управляющий партнёр Алексей '
                     'Захарько и советник практики недвижимости и ритейла Ольга Попель при '
                     'поддержке советника практики корпоративного права и M&A Дмитрия '
                     'Микрюкова. Источник: https://t.me/LawFirms/8221']],
        },
    },
]


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}

    for did, role, firm, note, url, before in ADVISORS:
        deal = by_id.get(did)
        assert deal is not None, 'карточки %s нет в базе' % did
        adv = (deal.get('law') or {}).get('adv') or []
        assert firm.lower() not in ' | '.join(str(a[1]) for a in adv if len(a) > 1).lower(), \
            '%s: %s уже записан' % (did, firm)
        assert [str(a[0]) for a in adv if a] == before, \
            '%s: роли другие (%r)' % (did, [str(a[0]) for a in adv if a])
        print('%s  %s' % (did, (deal.get('title') or '')[:60]))
        print('    + %s — %s' % (role, firm))

    for row in FILL:
        deal = by_id.get(row['id'])
        assert deal is not None, 'карточки %s нет в базе' % row['id']
        for key, value in row['expect'].items():
            assert deal.get(key) == value, \
                '%s: поле %s сейчас %r, а не %r — решение принимать заново' % (
                    row['id'], key, deal.get(key), value)
        assert row['url'] not in {str(s[1]) for s in (deal.get('src') or []) if len(s) > 1}, \
            '%s: объявление уже стоит в источниках' % row['id']
        print('%s  %s' % (row['id'], (deal.get('title') or '')[:60]))
        for key, value in row['set'].items():
            print('    %-11s -> %s' % (key, str(value)[:72]))
        for key in list(row.get('eco') or {}) + list(row.get('law') or {}):
            print('    заполняется: %s' % key)

    print('\nкарточек к правке: %d' % (len(ADVISORS) + len(FILL)))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0

    for did, role, firm, note, url, before in ADVISORS:
        deal = by_id[did]
        law = deal.setdefault('law', {})
        law.setdefault('adv', []).append([role, firm, note])
        deal.setdefault('src', []).append([SRC_LABEL, url])
    for row in FILL:
        deal = by_id[row['id']]
        deal.update(row['set'])
        # Полный набор ключей `eco`, а не только заполняемые: интерфейс во
        # многих местах читает `d.eco.rationale` без проверки (урок E9).
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

    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО в %s' % os.path.relpath(DATA, ROOT))
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
