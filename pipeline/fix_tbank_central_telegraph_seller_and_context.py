# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка g44aef88b
(Т-банк закрыл покупку здания Центрального телеграфа на Тверской улице)
— `seller` карточки нёс «VOS'HOD», хотя источник самой карточки прямо
называет продавцом другое юрлицо, а VOS'HOD — лишь девелопер, работавший
в его интересах.

Проверено лично прямым WebFetch (Ведомости, 05.02.2025, тот же источник,
что уже стоит в `src`): «Т-банк договорился с кипрской Riverstretch
Trading & Investments о выкупе у нее здания Центрального телеграфа» —
«Riverstretch Trading & Investments является акционером крупнейшего
владельца московских офисов класса А – O1 Properties», девелопер
Vos'hod работал «в интересах собственника здания» (Riverstretch), а не
как сам продавец. Независимо подтверждено CRE.ru (06.02.2025):
«Продавцом выступила кипрская Riverstretch Trading & Investments,
являющаяся акционером девелопера Vos'hod».

`seller`: «VOS'HOD» → «Riverstretch Trading & Investments (Кипр)».
`law.adv`: роль первой записи уточнена — Melling, Voitishkin & Partners
были консультантами настоящего продавца (Riverstretch), а не VOS'HOD.

`eco.context` (стоял прочерком) дополнен: торговая часть здания (CRE.ru:
«торговая составляющая на 15 тыс. кв. м» с якорным арендатором «Золотое
Яблоко»), ход ремонта корпоративного университета («ремонтные работы
закончатся в 2027 году», сайт университета Т-Банка cu.ru, 13.02.2025) и
предыдущая история актива (Интерфакс, 11.09.2019: «"Ростелеком" продал
свою долю в здании Центрального телеграфа» — 65% помещений, ~38 тыс.
кв. м, за 3,5 млрд рублей — покупателем выступила структура, связанная
с той же Riverstretch/O1 Properties).

НЕ ВКЛЮЧЕНО: утверждение, что покупателем по сделке 2025 года выступило
ООО «Центральный телеграф», — при прямой перепроверке источника это
оказалось смешением с историей 2019 года (тогда ООО «Центральный
телеграф» упоминается как СТОРОНА, купившая площади у «Ростелекома», а
не как участник сделки с Т-Банком); честной путаницы не переносим.
Точная сумма сделки по-прежнему не раскрыта — только разброс оценок
консультантов (35-43 млрд ₽), уже отражённый диапазоном 35-40 млрд ₽ в
top-level `sum`. Финансовые показатели самого здания как актива — ни в
одном источнике не публиковались отдельно.

Запуск: python3 pipeline/fix_tbank_central_telegraph_seller_and_context.py
        python3 pipeline/fix_tbank_central_telegraph_seller_and_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g44aef88b'

OLD_SELLER = "VOS'HOD"
NEW_SELLER = 'Riverstretch Trading & Investments (Кипр)'

OLD_SELLER_SRC = 'adv'
NEW_SELLER_SRC = 'text'

BUYER_ADV_ENTRY = [
    'Юридический консультант «Т-Технологии»/Т-Банка',
    'ALUMNI Partners',
    'Приобретение здания Центрального телеграфа на Тверской. Источник: pravo.ru',
]

OLD_ADV_ENTRY = [
    "Юридический консультант продавца (VOS'HOD)",
    'Melling, Voitishkin & Partners',
    "Продажа здания Центрального телеграфа на Тверской ул. Т-Банку. Источник: pravo.ru/company_news/257908",
]
NEW_ADV_ENTRY = [
    'Юридический консультант продавца (Riverstretch Trading & Investments)',
    'Melling, Voitishkin & Partners',
    "Продажа здания Центрального телеграфа на Тверской ул. Т-Банку; VOS'HOD — девелопер, работавший в интересах продавца, не сам продавец. Источник: pravo.ru/company_news/257908",
]

OLD_CONTEXT = '—'
NEW_CONTEXT = (
    'Торговая часть здания сохранена: «торговая составляющая на 15 тыс. '
    'кв. м» с якорным арендатором «Золотое Яблоко» (CRE.ru, 6 февраля '
    '2025 года). Ремонт под корпоративный университет Т-Банка идёт: '
    '«ремонтные работы закончатся в 2027 году» (сайт университета, '
    '13 февраля 2025 года). Предыдущая смена собственника: «"Ростелеком" '
    'продал свою долю в здании Центрального телеграфа» — 65% помещений '
    '(около 38 000 кв. м) — за 3,5 млрд рублей структуре, связанной с '
    'той же Riverstretch/O1 Properties (Интерфакс, 11 сентября 2019 '
    'года).'
)

NEW_SRC = [
    ['CRE.ru', 'https://cre.ru/news/97435'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['seller'] == OLD_SELLER
    assert deal['seller_src'] == OLD_SELLER_SRC
    assert deal['law']['adv'] == [BUYER_ADV_ENTRY, OLD_ADV_ENTRY]
    assert deal['eco']['context'] == OLD_CONTEXT

    new_src = deal['src'] + NEW_SRC

    print('=== seller: станет ===')
    print(NEW_SELLER)
    print('\n=== seller_src: станет ===')
    print(NEW_SELLER_SRC)
    print('\n=== law.adv: станет ===')
    print([BUYER_ADV_ENTRY, NEW_ADV_ENTRY])
    print('\n=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('\n=== src: добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['seller'] = NEW_SELLER
        deal['seller_src'] = NEW_SELLER_SRC
        deal['law']['adv'] = [BUYER_ADV_ENTRY, NEW_ADV_ENTRY]
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
