# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка gec433848 («Росатом»
купил 49% «Топ Системы»): дельта-поиск нашёл конкретный шаг интеграции
после сделки — меморандум с «Гринатомом» (ИТ-интегратором «Росатома») о
создании центра компетенций на базе T-FLEX PLM. Финансовые показатели
2024/2025 годов, которые агент также нашёл, НЕ переносятся: разные
источники (TAdviser, saby.ru, rbc.companies) подписывают близкие, но не
идентичные цифры разными годами (2024 vs 2025) без возможности сверить с
первичной отчётностью через доступные инструменты — переносить их значило
бы гадать. Реализация опциона на выкуп оставшихся 51% — не найдена,
попытка добросовестная (RBC, mergers.ru, TAdviser, it-world.ru,
planetacam.ru, Forbes, ФАС).

Запуск: python3 pipeline/fix_topsystems_grinatom_memorandum.py
        python3 pipeline/fix_topsystems_grinatom_memorandum.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gec433848'

OLD_STRUCT = '—'
NEW_STRUCT = (
    '2 июня 2025 года АО «Гринатом» (ИТ-интегратор «Росатома») и АО '
    '«Топ Системы» заключили меморандум о сотрудничестве по внедрению '
    'систем на базе T-FLEX PLM — с целью создания центра компетенций '
    'российского PLM-решения для его продвижения и тиражирования.'
)

NEW_SRC = ['tflex.ru', 'https://www.tflex.ru/about/news/detail/index.php?ID=5477']


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['law']['struct'] == OLD_STRUCT
    assert not any(s[1] == NEW_SRC[1] for s in deal['src'])

    print('=== law.struct: станет ===')
    print(NEW_STRUCT)
    print('=== src добавится ===', NEW_SRC)

    if write:
        deal['law']['struct'] = NEW_STRUCT
        deal['src'].append(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
