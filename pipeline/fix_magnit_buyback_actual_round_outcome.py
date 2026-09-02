# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка geb946158
(«"Магнит" выкупил свои акции у иностранных инвесторов с дисконтом») —
классическая ошибка «объявление принято за исход»: `sum`/`eco.sum`
(22,57 млрд ₽) и `date` (16 июня 2023) — это цифра и дата ОБЪЯВЛЕНИЯ
тендера на выкуп ДО 10% акций (10 191 135 акций × 2215 ₽), а не
реального закрытия. Тем же вечером/в течение двух недель лимит был
увеличен до 29,8%, и первый раунд реально закрылся 15 сентября 2023
года на 21,5% акций за 48,5 млрд ₽.

Проверено лично прямым WebFetch (Retail.ru,
https://www.retail.ru/news/magnit-vykupil-21-5-aktsiy-u-zarubezhnykh-investorov/):
«выкупила более 21,903 млн акций, что составляет около 21,5% от всех
выпущенных и находящихся в обращении акций за 48,5 млрд руб.»;
«расчеты происходили со 189 продавцами из 21 страны...»; дата — «15
сентября 2023».

Проверено лично прямым WebFetch (Retail.ru,
https://www.retail.ru/news/magnit-vykupil-29-7-svoikh-aktsiy-u-aktsionerov-nerezidentov/):
«По итогам двух тендерных предложений, объявленных 16 июня 2023 года и
10 октября 2023 года» + «двусторонней сделки в октябре 2023 года,
покупатель приобретет... 30 245 828,8 акций, что составляет около 29,7%
от всех выпущенных и находящихся в обращении акций»; второй тендер —
«7 899 569 акций (около 7,8%)» за «около 17,49 млрд руб.».

Пишу в карточку РЕЗУЛЬТАТ ПЕРВОГО РАУНДА (21,5%/48,5 млрд ₽,
15.09.2023) — именно он ближе всего по времени и предмету к тому, что
карточка изначально описывала (тендер, объявленный 16 июня), а не
общий трёхкомпонентный итог (29,7%): второй раунд и внебиржевая сделка
— это фактически отдельные события того же сюжета, зафиксированы в
`eco.context` текстом, но не смешаны с суммой/датой первого раунда.

НЕ ВКЛЮЧЕНО: точная дата окончательного расчёта по всем этапам (только
общая формулировка «январь 2024» без дословной проверенной цитаты
первички — Forbes и РБК не читаются через WebFetch, отдают
изображение/401); судьба выкупленного пакета (погашение/SPO/мотивация
сотрудников) — по данным на 2025 год решение компанией не объявлено,
не додумывается.

Запуск: python3 pipeline/fix_magnit_buyback_actual_round_outcome.py
        python3 pipeline/fix_magnit_buyback_actual_round_outcome.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'geb946158'

OLD_DATE = '2023-06-16'
NEW_DATE = '2023-09-15'

OLD_SUM = '22,57 млрд ₽'
NEW_SUM = '48,5 млрд ₽'

OLD_ECO_SHARE = '—'
NEW_ECO_SHARE = '21,5% акций (21,903 млн акций) — по итогам первого раунда тендера.'

OLD_ECO_CONTEXT = '—'
NEW_ECO_CONTEXT = (
    'Первоначальный лимит — 10% акций по 2215 ₽ (объявлен 16 июня 2023, '
    'вдвое ниже рыночной цены) — был увеличен до 29,8% из-за высокого '
    'спроса; первый раунд закрылся 15 сентября 2023 года на 21,5% (48,5 '
    'млрд ₽, расчёты со 189 продавцами из 21 страны). 10 октября 2023 '
    'объявлен второй раунд — ещё 7,8% акций за ~17,49 млрд ₽; вместе со '
    'внебиржевой сделкой итоговый пакет достиг 29,7% акций.'
)

NEW_SRC = [
    ['Retail.ru', 'https://www.retail.ru/news/magnit-vykupil-21-5-aktsiy-u-zarubezhnykh-investorov/'],
    ['Retail.ru', 'https://www.retail.ru/news/magnit-vykupil-29-7-svoikh-aktsiy-u-aktsionerov-nerezidentov/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['date'] == OLD_DATE
    assert deal['sum'] == OLD_SUM
    assert deal['eco']['sum'] == OLD_SUM
    assert deal['eco']['share'] == OLD_ECO_SHARE
    assert deal['eco']['context'] == OLD_ECO_CONTEXT

    new_src = deal['src'] + NEW_SRC

    print('=== date: станет ===')
    print(NEW_DATE)
    print('\n=== sum / eco.sum: станет ===')
    print(NEW_SUM)
    print('\n=== eco.share: станет ===')
    print(NEW_ECO_SHARE)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['date'] = NEW_DATE
        deal['sum'] = NEW_SUM
        deal['eco']['sum'] = NEW_SUM
        deal['eco']['share'] = NEW_ECO_SHARE
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
