# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка gdcda51be (ГАП «Ресурс»
купила группу компаний «Царицыно», ноябрь 2024): дельта-поиск нашёл два
класса новых фактов, оба подтверждены лично прямым WebFetch (New Retail
и Sostav.ru).

1. Финансовые показатели «Царицыно» за 2025 год (target_fin ранее нёс
   только данные 2023 года): выручка выросла на 3%, до 6,09 млрд руб.,
   чистая прибыль упала почти в четыре раза, до 47 млн руб.
2. Тревожный сигнал по всей группе ГАП «Ресурс»: три производственные
   площадки «Царицыно» остановлены с 22 июля до середины октября 2026
   года (заявленная причина — плановый капремонт), а к концу апреля 2026
   года к предприятиям ГРУППЫ подано свыше 560 исков на сумму более
   4,8 млрд руб. — это не факт о самой сделке, а сигнал финансового
   состояния покупателя уже после неё.

Не через review.py: факты из НОВЫХ источников для двух разных полей.

Запуск: python3 pipeline/fix_tsaritsyno_2026_halt_and_gap_resurs_lawsuits.py
        python3 pipeline/fix_tsaritsyno_2026_halt_and_gap_resurs_lawsuits.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gdcda51be'

OLD_TARGET_FIN = (
    'По итогам 2023 года чистая прибыль «Царицыно» составила 13,2 млн '
    'рублей при выручке 4,73 млрд рублей.'
)
TARGET_FIN_ADDITION = (
    ' В 2025 году выручка производственного ОАО «Царицыно» выросла на 3% '
    'год к году, до 6,09 млрд руб., чистая прибыль снизилась почти в '
    'четыре раза, до 47 млн руб. (Sostav.ru).'
)
NEW_TARGET_FIN = OLD_TARGET_FIN + TARGET_FIN_ADDITION

OLD_CONTEXT = (
    'Одной из крупнейших мясоперерабатывающих компаний в России, которая '
    'выпускает порядка 500 наименований колбас, принадлежат три завода в '
    'Москве и Московской области, которые могут выпускать около 150 тонн '
    'продукции в сутки, и торговый дом. По данным «СПАРК-Интерфакса», '
    'выручка группы в 2023 году составила 4,73 миллиарда рублей. (плюс '
    'четыре процента год к году).'
)
CONTEXT_ADDITION = (
    ' В 2026 году «Царицыно» остановил все три производственные площадки '
    '«до середины октября» — заявленная причина «плановый капитальный '
    'ремонт и реконструкция» (New Retail). Тревожный сигнал по всей '
    'группе-покупателю: «к концу апреля 2026 года к предприятиям группы '
    '[ГАП «Ресурс»] было подано свыше 560 исков на сумму более 4,8 млрд '
    'рублей» (тот же источник).'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['Sostav.ru', 'https://www.sostav.ru/publication/proizvoditel-kolbasy-tsaritsyno-priostanovil-postavki-produktsii-iz-za-remonta-85820.html'],
    ['New Retail', 'https://new-retail.ru/novosti/retail/tsaritsyno_priostanavlivaet_vypusk_produktsii/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['target_fin'] == OLD_TARGET_FIN
    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== eco.target_fin: станет ===')
    print(NEW_TARGET_FIN)
    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['target_fin'] = NEW_TARGET_FIN
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
