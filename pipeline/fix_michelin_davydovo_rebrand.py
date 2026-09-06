# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g688aa290` («Michelin продаёт завод по производству шин в России
компании Пауэр Интернешнл», май 2023, Закрыта) — судьба завода после
сделки не прослеживалась.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- rupec.ru/news/52429/: «Пауэр Интернэшнл-шины» приобрела площадку
  «весной 2023 года»; завод (в Давыдово) станет выпускать продукцию под
  новыми торговыми марками «Selna и Farlight»; сохранено «250 рабочих
  мест (в основном на единственном российском заводе Michelin в
  Давыдово»; плановая мощность — «до 2 млн покрышек в год».

НЕ ВНЕСЕНО: финансовые показатели завода после сделки — ни один из
проверенных источников их не публикует; неофициальное новое имя
площадки «Давыдово» как бренда (не путать с местом расположения,
которое подтверждено дословно) и состав шинных брендов для конечного
рынка (Sailun, Leao и др.) — встретились только в сниппетах отраслевых
магазинов (bs-tyres.ru, 4tochki.ru), не проверялись лично.

Запуск: python3 pipeline/fix_michelin_davydovo_rebrand.py
        python3 pipeline/fix_michelin_davydovo_rebrand.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g688aa290'

OLD_ECO_CONTEXT = (
    'В первом полугодии 2022 года компания списала 202 млн евро из-за '
    'приостановки работы на местном рынке. Балансовые риски ухода '
    'французская компания оценивала в общей сложности в 250 млн евро.'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' Завод в Давыдово продолжил работу под новым '
    'владельцем: сохранены 250 рабочих мест, выпуск переведён на новые '
    'торговые марки Selna и Farlight, плановая мощность — до 2 млн шин '
    'в год.'
)

OLD_SRC = [
    ['Интерфакс', 'https://www.interfax.ru/business/903364'],
]
NEW_SRC = OLD_SRC + [
    ['RUPEC', 'https://rupec.ru/news/52429/'],
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
