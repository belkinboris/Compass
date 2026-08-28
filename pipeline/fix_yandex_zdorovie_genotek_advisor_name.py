# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g8ef19fd4 (Яндекс продал
телемедицинский сервис «Яндекс.Здоровье» компании Genotek): `law.adv` уже
называл фирму-консультанта продавца (BIRCH), но не конкретного юриста —
дельта-поиск нашёл имя со страницы самого юриста. Подтверждено лично
прямым WebFetch.

«консультирование Яндекс в связи с продажей Genotek направления
телемедицины (под брендом Яндекс Здоровье)» — старший советник BIRCH
Виталий Колосков (birchlegal.ru).

Юридического консультанта покупателя (Genotek) и финансового консультанта
с любой стороны дельта-поиск не нашёл ни в одном источнике — честная
пустота, не тронуто. Итоговую сумму сделки прояснить не удалось — в
карточке остаётся только оценка аналитика.

Запуск: python3 pipeline/fix_yandex_zdorovie_genotek_advisor_name.py
        python3 pipeline/fix_yandex_zdorovie_genotek_advisor_name.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g8ef19fd4'

OLD_ADV = [
    ['Юридический консультант продавца (Яндекс)', 'BIRCH',
     'Продажа Яндекс.Здоровье компании Genotek. Источник: birchlegal.ru'],
]
NEW_ADV = [
    ['Юридический консультант продавца (Яндекс)', 'BIRCH',
     '«Консультирование Яндекс в связи с продажей Genotek направления '
     'телемедицины (под брендом Яндекс Здоровье)» — проект вёл старший '
     'советник BIRCH Виталий Колосков. Источник: birchlegal.ru'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['law']['adv'] == OLD_ADV

    print('=== law.adv: станет ===')
    print(NEW_ADV)

    if write:
        deal['law']['adv'] = NEW_ADV
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
