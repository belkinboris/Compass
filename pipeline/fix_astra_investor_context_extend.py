# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g9d9e7ab6 («Группа Астра»
ведёт переговоры о продаже до 20% капитала): дельта-поиск нашёл две новых
детали из независимых источников, вышедших позже уже прочитанных РБК Pro
и Forbes, — оценку личной сделки Фролов/Т1 и майское подтверждение
гендиректора, что компания по-прежнему открыта инвестору. Не через
review.py: комбинация фактов из ДВУХ разных новых источников (vedomosti.ru
и smart-lab.ru) в одном поле, ни один из которых не покрывает весь текст
целиком.

Запуск: python3 pipeline/fix_astra_investor_context_extend.py
        python3 pipeline/fix_astra_investor_context_extend.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g9d9e7ab6'

OLD_CONTEXT = (
    'В январе 2026 года первым названным кандидатом был «Росатом» — как '
    'стратегический партнёр для интеграции решений в инфраструктурные '
    'проекты. К весне 2026 года в переговоры вошёл также 1С — крупнейший '
    'российский разработчик ERP-систем, а «Росатом» и несколько крупнейших '
    'банков остаются в числе заинтересованных сторон. Отдельно от этого: '
    'мажоритарный акционер «Группы Астра» Денис Фролов ведёт переговоры о '
    'продаже 10–15% СОБСТВЕННЫХ акций IT-холдингу Т1 — это сделка о личном '
    'пакете акционера, а не о привлечении капитала в саму компанию.'
)

CONTEXT_ADDITION = (
    ' Сделка Фролова с Т1 оценивается примерно в 6–9 млрд руб.; причина '
    'продажи — необходимость расплатиться по собственным долгам, часть его '
    'акций находится в залоге у ВТБ. В мае 2026 года гендиректор «Астры» '
    'подтвердил, что компания «не исключает вариант привлечения крупного '
    'стратегического инвестора», отметив: «Фундаментально мы должны стоить '
    'сильно дороже».'
)

NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['vedomosti.ru', 'https://www.vedomosti.ru/technology/articles/2026/05/19/1198452-it-holding-mozhet-stat'],
    ['smart-lab.ru', 'https://smart-lab.ru/blog/news/1305007.php'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, 'eco.context изменился с момента чтения — проверьте'
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== eco.context: было ===')
    print(OLD_CONTEXT)
    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src: добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
