# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g9995eb50 («Страна
девелопмент» купила участок на 13,6 га в Марьино за 8,8 млрд руб.,
декабрь 2024): дельта-поиск нашёл, что сумма 8,8 млрд ₽ — это оценка
октября 2022 года (на этапе одобрения советом директоров покупателя), а
не подтверждённая цена закрытия декабря 2024-го; независимого источника с
итоговой ценой на момент закрытия не нашлось. Строительство первой
очереди начато (разрешение — август 2024, продажи — с октября 2024),
проект называется «Страна.Заречная» (рабочее название «Страна.Иловайская»),
застройщик по проектной декларации — АО «Специализированный застройщик
«Деметра»» (структура, которой ранее принадлежали участки ЦФТ). `eco.
context` сейчас пустая заглушка «—». Не через review.py: цитаты из
НЕСКОЛЬКИХ новых источников объединены в одно связное предложение.

Запуск: python3 pipeline/fix_strana_marino_project_name_context.py
        python3 pipeline/fix_strana_marino_project_name_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g9995eb50'

OLD_CONTEXT = '—'
NEW_CONTEXT = (
    'Сумма 8,8 млрд ₽ — оценка октября 2022 года, сделанная на этапе '
    'одобрения сделки советом директоров покупателя («Ведомости»: '
    '«покупная цена за 100% ЦФТ не должна превышать 8,8 млрд руб.»); '
    'независимого источника с итоговой ценой на момент закрытия в '
    'декабре 2024 года не нашлось. Прямым покупателем выступило ООО '
    '«Элит строй», принадлежащее «Стране девелопмент». Строительство '
    'первой очереди начато: разрешение получено в августе 2024 года, '
    'продажи стартовали в октябре того же года. Проект называется '
    '«Страна.Заречная» (рабочее название «Страна.Иловайская»), '
    'застройщик по проектной декларации — АО «Специализированный '
    'застройщик «Деметра»» (структура, которой ранее принадлежали '
    'участки ЦФТ); строительство разделено на три очереди со сроком '
    'завершения к 2030 году.'
)

NEW_SRC = [
    ['Ведомости', 'https://www.vedomosti.ru/realty/articles/2022/10/25/947160-investkompaniya-a1-i-partneri-nashli-novogo-pretendenta'],
    ['ВсеНовостройки.ру', 'https://vsenovostroyki.ru/customer/22511'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
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
