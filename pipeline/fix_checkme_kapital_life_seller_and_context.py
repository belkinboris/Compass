# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка gfe151394
(Страховая компания «Капитал Life» приобрела 100% Checkme). Дельта-поиск
нашёл продавца (карточка его не называла вовсе) и атрибуцию уже стоявшей
оценки суммы. Проверено лично прямым WebFetch.

1) `seller` (новое поле) — RB.ru, дословно: «Checkme основала
предпринимательница Анастасия Файзуленова в 2020 году.» Источник статьи
целиком посвящён именно этой сделке (её выходу из бизнеса), поэтому
основательница — она же продавец на момент сделки, а не просто
исторический факт основания (см. правило CLAUDE.md «Основатель компании
— не то же самое, что её нынешний владелец» — здесь, в отличие от того
случая, статья описывает саму продажу, а не историю компании в отрыве
от сделки).
Источник: https://rb.ru/news/chekme-exit/

2) `eco.val` — атрибуция уже стоявшей оценки: ASN-news, дословно: «С
учетом финансовых показателей за последние три года и объема предыдущих
инвестиций в компанию, сумму сделки по продаже 100% Checkme можно
оценить в 130 млн рублей», — сообщил аналитик ФГ «Финам» Леонид
Делицын.» Раньше поле называло оценку без имени оценщика.
Источник: https://www.asn-news.ru/news/86955 (уже в src)

3) `eco.context` (новое поле) — цифровая поликлиника «LIFE.клиника»
реально работает по состоянию на 2026 год: в подвале её сайта указано
«© 2019—2026 ООО «КЭРИФАЙ»» — то есть сервис активен и остался на прежнем
юрлице (бывший Checkme), а не передан отдельной структуре «Капитал
Life».
Источник: https://life-clinica.ru/

НЕ включены: консультанты сделки — не найдены ни в одном из 8 проверенных
источников; операционные результаты клиники (число пациентов, выручка) —
источники дают только общие финансовые показатели «Капитал Life» целиком,
не привязанные к клинике отдельно; цитата Файзуленовой из Forbes — не
удалось лично проверить (WebFetch отдал нечитаемое содержимое страницы),
поэтому не используется.

Запуск: python3 pipeline/fix_checkme_kapital_life_seller_and_context.py
        python3 pipeline/fix_checkme_kapital_life_seller_and_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gfe151394'

NEW_SELLER = 'Анастасия Файзуленова (основательница Checkme)'

OLD_VAL = 'По оценкам экспертов; 100–130 млн ₽ (по оценке)'
NEW_VAL = (
    'Аналитик ФГ «Финам» Леонид Делицын оценил сумму сделки: «С учетом '
    'финансовых показателей за последние три года и объема предыдущих '
    'инвестиций в компанию, сумму сделки по продаже 100% Checkme можно '
    'оценить в 130 млн рублей».'
)

OLD_CONTEXT = '—'
NEW_CONTEXT = (
    'Цифровая поликлиника «LIFE.клиника» работает по состоянию на 2026 '
    'год на прежнем юрлице: в подвале её сайта указано «© 2019—2026 ООО '
    '«КЭРИФАЙ»» (бывший Checkme).'
)

NEW_SRC = [
    ['life-clinica.ru', 'https://life-clinica.ru/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal.get('seller') is None
    assert deal['eco']['val'] == OLD_VAL
    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print(f'=== seller (новое поле): станет {NEW_SELLER!r} ===')
    print('=== eco.val: было ===')
    print(OLD_VAL)
    print('=== eco.val: станет ===')
    print(NEW_VAL)
    print('=== eco.context (новое поле): станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['seller'] = NEW_SELLER
        deal['eco']['val'] = NEW_VAL
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
