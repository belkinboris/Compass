# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`gd607171c` («"Протек" купил производителя фармсубстанций "Бион"»,
февраль 2023, Закрыта) — финансовая динамика предприятия после сделки
не прослеживалась.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- audit-it.ru/contragent/1034004209887_ooo-bion: «выручку в сумме 1,4
  млрд руб., что на 2,7 млн руб., или на 0,2%, меньше, чем годом
  ранее» (2025 год) и «прибыль в размере 47,1 млн руб.» — при этом
  прибыль 2024 года (~148 млн ₽) была почти втрое больше; «с
  02.02.2023» текущий учредитель — «АО "ПРОТЕК"».

НЕ ВНЕСЕНО: (1) заявленное в пресс-релизе «Фармвестника» «активное
развитие направления производства субстанций» — финансовые показатели
2024-2025 годов (выручка не растёт, прибыль резко упала) этому не
соответствуют, но прямых новостей об инвестициях, новых продуктах или
расширении производства не нашлось — противоречие оставлено как есть,
без домысливания причины; (2) дальнейшие сделки Михаила Шелкова в
фармацевтике — не нашлось; единственный смежный проект (учреждение в
январе 2024 года ООО «Медицинский титан», производство медизделий из
титана в ОЭЗ «Технополис Москва») — это медтех/имплантология, не
фармацевтика в узком смысле, и не проверен личным чтением
первоисточника.

Запуск: python3 pipeline/fix_protek_bion_2025_financials.py
        python3 pipeline/fix_protek_bion_2025_financials.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gd607171c'

OLD_ECO_CONTEXT = (
    'Химико-фармацевтическая компания «Бион» создана в 2003 году, её '
    'предприятие по выпуску субстанций работает в Обнинске Калужской '
    'области. В портфеле компании антиоксиданты, анестетики, '
    'бета-адреноблокаторы, антикоагулянты, противоопухолевые и '
    'противовирусные средства.'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' По итогам 2025 года выручка «Биона» осталась '
    'на уровне 1,4 млрд ₽ (практически не изменилась к 2024 году), а '
    'прибыль упала почти втрое — до 47,1 млн ₽.'
)

OLD_SRC = [
    ['Vademecum', 'https://vademec.ru/news/2023/02/06/protek-kupil-proizvoditelya-farmsubstantsiy-u-osnovnogo-vladeltsa-vsmpo-avisma/'],
    ['Ведомости', 'https://www.vedomosti.ru/business/articles/2023/02/07/961917-protek-vikupil-u-shelkova-aktivi-bion'],
]
NEW_SRC = OLD_SRC + [
    ['audit-it.ru', 'https://www.audit-it.ru/contragent/1034004209887_ooo-bion'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['src'] == OLD_SRC

    print('=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: станет ===')
    print(NEW_SRC)

    if write:
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
