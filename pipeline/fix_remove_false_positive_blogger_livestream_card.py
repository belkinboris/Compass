# -*- coding: utf-8 -*-
"""Почасовой приток 4 сентября 2026 (~15:20) — ворота пропустили карточку,
не являющуюся сделкой M&A: «Блогер из КНР Даньдань продала товары РФ более
чем на 1 млрд рублей за время ВЭФ» (ТАСС) — это розничная выручка со
стрима блогера-инфлюенсера («Ян Жуньсинь провела стрим во Владивостоке,
его охваты за семь часов превысили 30 млн человек»), а не покупка/продажа
компании или актива. Автоматический разбор принял оборот «продала товары
... на 1 млрд рублей» за структуру «продавец — сумма сделки» и создал
карточку с `seller`="Блогер из КНР Даньдань", `asset`="товары РФ более чем
на 1 млрд рублей" — бессмыслица уровня уже известного класса ложных
срабатываний (макро-статистика розницы/фондового рынка, см.
PRODUCT_ROADMAP.md, третий такой случай за сегодня по другому шаблону).

Правило регулярки НЕ пишется на ходу (это отдельная, измеренная задача
для прогона «качество») — карточка снимается из pending.json точечно,
тем же способом, что уже применялся к другим ложным находкам ворот.

Запуск: python3 pipeline/fix_remove_false_positive_blogger_livestream_card.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING_PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')

REMOVE_ID = 'ga42672ed'


def main(write=False):
    with open(PENDING_PATH, encoding='utf-8') as f:
        pending = json.load(f)

    before = len(pending['cards'])
    matches = [c for c in pending['cards'] if c['id'] == REMOVE_ID]
    assert len(matches) == 1, f'ожидалась ровно одна карточка {REMOVE_ID}, найдено {len(matches)}'
    assert matches[0]['seller'] == 'Блогер из КНР Даньдань'

    pending['cards'] = [c for c in pending['cards'] if c['id'] != REMOVE_ID]
    after = len(pending['cards'])
    assert after == before - 1

    print(f'Снята ложная карточка {REMOVE_ID} (не сделка M&A, розничный стрим-эфир).')

    if write:
        with open(PENDING_PATH, 'w', encoding='utf-8') as f:
            json.dump(pending, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Записано.')
    else:
        print('(сухой прогон, для записи — --write)')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
