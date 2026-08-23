# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g0a6cea12 (Полюс/ЮГК,
месторождение «Марокское»): дельта-поиск нашёл более точную разбивку
запасов по категориям — в карточке была только округлённая сумма
«более 60 тонн» в `extra`, а разбивка по категориям (Р1/Р2/С2) нигде не
приводилась.

Источник: zolteh.ru — читал напрямую. Не через review.py: продолжение
уже заполненного `eco.share` другим фрагментом того же источника.
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g0a6cea12'
OLD_SHARE = (
    'По словам финдиректора ЮГК Артема Клецкина, Марокское '
    'месторождение отличается высоким содержанием золота — более 2 '
    'граммов на тонну, а процесс извлечения золота такой же, как на '
    'действующих производственных мощностях в регионе '
    '[гравитационно-цианистая схема извлечения]'
)
ADDITION = (
    'Апробированные прогнозные ресурсы Марокского рудного поля '
    'составляют по категории Р1 53 т золота (содержание 2,2 г/т), Р2 — '
    '15,6 т (1,8 г/т); ожидаемые запасы С2 — 25,3 т (2,11 г/т).'
)
NEW_SHARE = OLD_SHARE + ' ' + ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['share'] == OLD_SHARE, \
        f"eco.share: неожиданное значение {deal['eco']['share']!r}"

    print(f"{CARD_ID} eco.share: += разбивка запасов по категориям "
          "(Р1/Р2/С2)")
    deal['eco']['share'] = NEW_SHARE

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО")
    else:
        print("Сухой прогон. Запись — с --write.")


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
