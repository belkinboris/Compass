# -*- coding: utf-8 -*-
"""Карточка gec433848 (Росатом купил 49% «Топ Системы»): перечитывание
после записи (REVISION_BRIEF.md, «после правки — перечитайте карточку
целиком») нашло, что pipeline/fix_topsystems_grinatom_memorandum.py
положил факт про меморандум с «Гринатомом» в `law.struct` — но это
интеграционная новость ПОСЛЕ сделки, а не структура самой сделки
(доли, форма расчётов). Переносится в `eco.context`, где уже лежат
другие факты о деятельности компании после/вокруг сделки.

Запуск: python3 pipeline/fix_topsystems_grinatom_move_to_context.py
        python3 pipeline/fix_topsystems_grinatom_move_to_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gec433848'

MEMO_TEXT = (
    '2 июня 2025 года АО «Гринатом» (ИТ-интегратор «Росатома») и АО '
    '«Топ Системы» заключили меморандум о сотрудничестве по внедрению '
    'систем на базе T-FLEX PLM — с целью создания центра компетенций '
    'российского PLM-решения для его продвижения и тиражирования.'
)

OLD_STRUCT = MEMO_TEXT
NEW_STRUCT = '—'

OLD_CONTEXT = (
    'Компания поставляет свои разработки Объединенной авиастроительной '
    'корпорации (ОАК) в рамках проекта по внедрению единой '
    'информационной среды для управления процессами разработки (общая '
    'стоимость — 3,1 млрд руб.). Также «Топ Системы» участвуют в '
    'проекте «Роскосмоса» по разработке единой информационной среды для '
    'управления жизненным циклом изделий ракетно-космической техники.'
)
NEW_CONTEXT = OLD_CONTEXT + ' ' + MEMO_TEXT


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['law']['struct'] == OLD_STRUCT
    assert deal['eco']['context'] == OLD_CONTEXT

    print('=== law.struct: станет ===', repr(NEW_STRUCT))
    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)

    if write:
        deal['law']['struct'] = NEW_STRUCT
        deal['eco']['context'] = NEW_CONTEXT
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
