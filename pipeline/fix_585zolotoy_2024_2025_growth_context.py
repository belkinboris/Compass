# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g51fbc8c8 (Искандар
Махмудов и Андрей Бокарев вошли в капитал ювелирной сети «585 Золотой»,
декабрь 2024): дельта-поиск нашёл, что доли инвесторов (Виолан/Элариум по
4,65%) за восемь месяцев не изменились — по данным companies.rbc.ru на
25 августа 2026 года структура собственности идентична зафиксированной в
карточке сразу после сделки, значит инвестиция была разовой, а не первым
шагом к наращиванию доли. Заодно нашлись свежие показатели самой сети:
выручка «Регент Голд» за 2024 год выросла до 37,6 млрд ₽ (+28,5% к 2023),
прибыль — 962,2 млн ₽; в 2025 году открыто ~128 новых магазинов, сеть
выросла до 1000+ точек в 420 городах. Не через review.py: цифры за
2024-2025 год из реестровых агрегаторов и отраслевого СМИ (new-retail.ru),
объединённые в одно предложение, а не дословный кусок одной статьи.

Запуск: python3 pipeline/fix_585zolotoy_2024_2025_growth_context.py
        python3 pipeline/fix_585zolotoy_2024_2025_growth_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g51fbc8c8'

OLD_TARGET_FIN = (
    'По итогам 2023 года «Регент Голд» получила выручку свыше 29 млрд '
    'рублей и имела более 600 подразделений в разных городах страны.'
)
TARGET_FIN_ADDITION = (
    ' По итогам 2024 года выручка выросла до 37,6 млрд ₽ (+28,5%), '
    'чистая прибыль составила 962,2 млн ₽. В 2025 году сеть открыла '
    'около 128 новых магазинов и выросла до более чем 1000 точек в 420 '
    'городах России. Доли инвесторов Махмудова и Бокарева (по 4,65% '
    'через «Виолан» и «Элариум») с момента сделки не менялись — по '
    'состоянию на 25 августа 2026 года структура собственности осталась '
    'той же, что зафиксирована сразу после сделки.'
)
NEW_TARGET_FIN = OLD_TARGET_FIN + TARGET_FIN_ADDITION

NEW_SRC = [
    ['New Retail', 'https://new-retail.ru/novosti/retail/set_585_zolotoy_podvela_itogi_razvitiya_v_2025_godu/'],
    ['РБК Компании', 'https://companies.rbc.ru/id/1137847109861-585zolotoj/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['target_fin'] == OLD_TARGET_FIN
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== eco.target_fin: станет ===')
    print(NEW_TARGET_FIN)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['target_fin'] = NEW_TARGET_FIN
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
