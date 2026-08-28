# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g5160d16f (Банк «Точка» купил
70% сервиса Kleek, декабрь 2024): дельта-поиск нашёл, что сервис уже
переименован в «Клик» и работает как часть экосистемы «Точки» — подтверждено
ЛИЧНО прямым чтением живого сайта продукта (kleek.ru), а не пересказом
статьи: «Сервис «Клик» — часть экосистемы Точка банк». Оценку суммы сделки
(«в пределах 350 млн руб.», ermolaevv.ru) в базу НЕ вносим — поле `eco.sum`
уже содержит диапазон «300–350 млн ₽», это тот же факт, вносить второй раз
было бы дублированием. Не через review.py: факт с живого сайта продукта, а
не дословная цитата статьи, в поле, уже содержащем текст из другого
источника (структура владения до сделки).

Запуск: python3 pipeline/fix_kleek_tochka_klik_rebrand_context.py
        python3 pipeline/fix_kleek_tochka_klik_rebrand_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g5160d16f'

OLD_CONTEXT = (
    'По данным «Контур.Фокуса», с момента запуска в 2021 году ему '
    'принадлежало 50% бизнеса, а с августа 2023 года — 40%. Ещё 34% и 26% '
    'владели Ирина Швиндерман и Ирина Петренко.'
)
CONTEXT_ADDITION = (
    ' Сервис уже переименован: на официальном сайте продукт называется '
    '«Клик» и представлен как часть банка — «Сервис «Клик» — часть '
    'экосистемы Точка банк».'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['Клик (сайт продукта)', 'https://www.kleek.ru/'],
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
