# -*- coding: utf-8 -*-
"""Месячная очередь, карточка g5880d206 (Игорь Ким/«Фольксваген банк
Рус»): дельта-поиск нашёл (1) точную структуру владения — Ким получил
45% напрямую и 55% через подконтрольную «Экспомобилити», то есть
100% под ОДНИМ конечным бенефициаром, а не совместная сделка с
«Экспомобилити» как отдельной стороной, и (2) что случилось после
закрытия — банк переименован в «Пихта Банк» (28 апреля 2025).

Не через `review.py`: оба факта из НОВЫХ источников (Интерфакс,
bosfera.ru), не образуют с уже записанным текстом непрерывный кусок.

Источники — читал напрямую (WebFetch, дословные цитаты подтверждены):
https://www.interfax.ru/business/1010853
https://bosfera.ru/press-release/folksvagen-bank-rus-smenil-nazvanie-na-pihta-bank

Запуск: python3 pipeline/fix_kim_volkswagen_bank_structure_and_rename.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g5880d206'

OLD_STRUCT = (
    'С учетом обязательного дисконта к рыночной стоимости актива '
    'покупка обойдется новым собственникам значительно ниже значения '
    'капитала. В частности, с октября 2024 года минимальный дисконт '
    'к рыночной цене при продаже составляет 60%.'
)
STRUCT_ADDITION = (
    ' Бизнесмен получил 45% долей в банке напрямую и еще 55% – через '
    'контролируемую им компанию "Экспомобилити" — то есть 100% под '
    'одним конечным бенефициаром, а не раздельными сторонами.'
)
NEW_STRUCT = OLD_STRUCT + STRUCT_ADDITION

OLD_CONTEXT = (
    'Ранее Фольксваген Банк Гмбх владел 1%, Фольксваген Файненшл '
    'Сервисез Оверсиз Акциенгезелльшафт — 99%.'
)
CONTEXT_ADDITION = (
    ' После сделки, 28 апреля 2025 года, «Фольксваген Банк РУС» '
    'сменил название на «Пихта Банк» (англоязычная версия — PIKHTA '
    'BANK LLC).'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['law']['struct'] == OLD_STRUCT, \
        f"law.struct: неожиданное значение {deal['law']['struct']!r}"
    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"

    print(f'{CARD_ID} law.struct: += структура владения (45%+55% под '
          f'одним бенефициаром)')
    print(f'{CARD_ID} eco.context: += переименование в «Пихта Банк» '
          f'после сделки')

    if write:
        deal['law']['struct'] = NEW_STRUCT
        deal['eco']['context'] = NEW_CONTEXT
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('ЗАПИСАНО')
    else:
        print('Сухой прогон. Запись — с --write.')


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
