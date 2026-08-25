# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g5a22a31a (агрохолдинг
«Степь» продаёт портовые активы в Азове и Волгодонске): дельта-поиск
подтвердил, что покупатель и цена по-прежнему не названы нигде спустя
год, но нашёл независимый источник (РБК Ростов, тот же день, что и уже
прочитанный Коммерсантъ), называющий конкретную цифру долга АФК
«Система», о снижении которого шла речь в уже записанном предложении.
Не через review.py: цифра из ВТОРОГО источника расширяет предложение,
построенное на первом, а не лежит в нём целиком.

Запуск: python3 pipeline/fix_step_azov_debt_context.py
        python3 pipeline/fix_step_azov_debt_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g5a22a31a'

OLD_CONTEXT = (
    'Один из источников издания отметил, что их продажа могла бы помочь '
    'снизить долговую нагрузку АФК «Система».'
)

CONTEXT_ADDITION = (
    ' По итогам первого квартала 2025 года чистый долг АФК «Система» '
    'увеличился до 327,9 млрд руб.'
)

NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = ['rostov.rbc.ru', 'https://rostov.rbc.ru/rostov/freenews/6888ca1e9a7947c2401948f6']


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, 'eco.context изменился с момента чтения — проверьте'
    assert not any(s[1] == NEW_SRC[1] for s in deal['src']), 'источник уже в src'

    print('=== eco.context: было ===')
    print(OLD_CONTEXT)
    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src: добавится ===')
    print(NEW_SRC)

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].append(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
