# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g1c47b363 (ГК «Таврос»
приобрела 33% ООО «МПК «Тосненский»», декабрь 2024): дельта-поиск нашёл, что
11 августа 2025 года все три совладельца, получившие долю одновременно с
«Тавросом» (АО «Виннер», Андрей Шутилин, Ирина Шушаначева), одновременно
вышли из состава участников (ЕГРЮЛ через audit-it.ru) — «Таврос» стал
единоличным собственником комбината (100%). Тот же временной паттерн, что и
в сестринской сделке того же холдинга (United buns/«Багерстат Рус», где
аналогичная промежуточная структура с тем же АО «Виннер» и тем же Шутилиным
разрешилась в мае 2025 года — карточка g5b4a3bf8), только здесь на три
месяца позже. Бенефициар АО «Виннер» по-прежнему нигде не раскрыт, механизм
и цена выкупа долей не освещались прессой — честная пустота остаётся
пустотой. Подтверждено независимо (AKM.RU, апрель 2026) свежими финансовыми
показателями за 2025 год. Не через review.py: цитаты из НОВЫХ источников
(audit-it.ru, akm.ru) в поле, уже содержащем текст из других источников.

Запуск: python3 pipeline/fix_tosnenskiy_tavros_full_consolidation.py
        python3 pipeline/fix_tosnenskiy_tavros_full_consolidation.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g1c47b363'

OLD_CONTEXT = (
    'Связаться с бывшими собственниками предприятия — Олегом Селиховым '
    '(37%), Екатериной Ясновой (36%) и Виктором Крыловым (27%; ему также '
    'принадлежит мясоперерабатывающий завод «Иней» в Санкт-Петербурге) — '
    'не удалось. Судя по данным СПАРК, они полностью вышли из бизнеса МПК '
    '«Тосненский».'
)
CONTEXT_ADDITION = (
    ' 11 августа 2025 года все три совладельца, получившие долю '
    'одновременно с «Тавросом» (АО «Виннер», Андрей Шутилин, Ирина '
    'Шушаначева), одновременно вышли из состава участников — «Таврос» '
    'стал единоличным собственником комбината (100%), следует из ЕГРЮЛ. '
    'Бенефициар АО «Виннер», а также механизм и цена выкупа долей '
    'по-прежнему нигде не раскрыты. По итогам 2025 года выручка МПК '
    '«Тосненский» выросла до 7,594 млрд руб. (с 6,82 млрд в 2023-м), '
    'чистая прибыль — до 65 млн руб. (с 40 млн), чистые активы — 379 млн '
    'руб.'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['audit-it.ru', 'https://www.audit-it.ru/contragent/1044701893389_ooo-mpk-tosnenskiy'],
    ['AKM.RU', 'https://www.akm.ru/analyt/chistye_aktivy_agrokholdinga_tavros_snizilis_na_10_po_itogam_2025_goda_/'],
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
