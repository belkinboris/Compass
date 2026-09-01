# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
g8368bb6c (Baring Vostok продал ПКБ Роману Ковалеву, 25.09.2023,
статус «Закрыта») — компания выросла и укрепила лидерство на рынке
коллекторских агентств, структура собственности не менялась.

Проверено лично прямым WebFetch (рейтинговое агентство НКР,
29.01.2026): чистая прибыль ПКБ выросла с 6,5 млрд руб. (2023) до 8,6
млрд руб. (2025), активы — с 25,1 до 30,5 млрд руб., объём купленных
долговых портфелей — с 15,4 до 28,5 млрд руб.; «В составе
топ-менеджмента компании не произошло существенных изменений после
смены акционеров в сентябре 2023 года».

НЕ ВКЛЮЧЕНО: доля рынка ПКБ совместно с «ЭОС» (~50% рынка, >20% по
цессии) — по данным саб-агента (Эксперт РА/Frank Media), не
дозаверено отдельным WebFetch; квартальные показатели 2025 года — из
вторичного разбора (smart-lab.ru), не дозаверено; другие инвестиции
Романа Ковалева — саб-агент не нашёл ничего нового.

Запуск: python3 pipeline/fix_pkb_kovalev_growth_and_market_share.py
        python3 pipeline/fix_pkb_kovalev_growth_and_market_share.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g8368bb6c'

OLD_EXTRA = (
    'Сделка по продаже 100% акций НАО «Первого коллекторского бюро» '
    'инвестором Baring Vostok (52,1% через FCB Holding Cooperatief '
    'U.A., Нидерланды) российскому бизнесмену Роману Ковалеву через '
    'его компанию «Тинсайд». В структуре капитала ПКБ также '
    'участвовали инвестфонд Da Vinci Capital и основатель Сергей '
    'Власов.'
)
NEW_EXTRA = OLD_EXTRA + (
    ' Компания выросла: чистая прибыль поднялась с 6,5 млрд руб. '
    '(2023) до 8,6 млрд руб. (2025), активы — с 25,1 до 30,5 млрд '
    'руб. Состав акционеров и топ-менеджмента с момента сделки '
    'существенно не менялся.'
)

NEW_SRC = [
    ['НКР', 'https://ratings.ru/ratings/press-releases/PKB-RA-290126/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['extra'] == OLD_EXTRA

    new_src = deal['src'] + NEW_SRC

    print('=== extra: станет ===')
    print(NEW_EXTRA)
    print('\n=== src: добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['extra'] = NEW_EXTRA
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
