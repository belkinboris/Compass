# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
gdf91b653 (Сбербанк Инвестиции приобрела 25% компании-собственника
складского комплекса «Крекшино», статус «Закрыта») — ни один из двух
предполагавшихся сценариев (выкуп доли обратно или переход всего
комплекса банку) не подтвердился; найден лишь косвенный факт о
финансовом состоянии девелопера НА УРОВНЕ ХОЛДИНГА.

Проверено лично прямым WebFetch (Ведомости, 03.09.2025): «Выручка
Malltech Holding по итогам 2024 г. составила 13,4 млрд руб. (+15% год
к году), чистая прибыль – 6,8 млрд руб. (-41%)» — холдинг финансово
устойчив, признаков банкротства нет. В августе 2025 года на уровне
холдинга сменился миноритарный акционер: «Balchug Capital... выкупил
этот пакет [16,96%] у фирмы Bardsley Realty... с Сейшельских островов»
— это структура ВСЕГО Malltech Holding (владеет также ТРЦ «Планета»,
«Лето», «Аура»), а не конкретной SPV «Вудвелл инвестментс»/«Феникс-К»,
которой посвящена эта карточка — прямой связи с долей Сбербанка в
источниках нет.

НЕ ВКЛЮЧЕНО: реализация одного из двух сценариев (выкуп доли Malltech
обратно или переход комплекса банку) — ни один источник 2023-2026
годов (Ведомости, CRE.ru, mergers.ru, РИА Недвижимость) её не
подтверждает; новых арендаторов или реконструкции самого логопарка
«Крекшино» за 2024-2026 годы не найдено.

Запуск: python3 pipeline/fix_krekshino_malltech_holding_health.py
        python3 pipeline/fix_krekshino_malltech_holding_health.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gdf91b653'

OLD_EXTRA = (
    'Сбербанк Инвестиции приобрела почти 25% компании, владеющей '
    'складским комплексом «Крекшино» площадью 253 000 кв.м. По '
    'предположению, Malltech передал долю в ходе реструктуризации '
    'долгов, так как Сбербанк является кредитором логопарка. '
    'Девелопер может впоследствии выкупить долю или передать банку '
    'весь комплекс.'
)
NEW_EXTRA = OLD_EXTRA + (
    ' Ни один из этих сценариев публично не подтвердился к 2026 году. '
    'На уровне холдинга Malltech (владеет также ТРЦ «Планета», «Лето», '
    '«Аура») дела идут устойчиво: выручка 2024 года — 13,4 млрд руб. '
    '(+15%), в августе 2025 сменился лишь миноритарный акционер '
    '(16,96% выкупил фонд Balchug Capital) — прямой связи с долей '
    'Сбербанка в этой конкретной SPV источники не называют.'
)

NEW_SRC = [
    ['Ведомости', 'https://www.vedomosti.ru/realty/articles/2025/09/03/1136115-u-upravlyayuschego-torgovimi-tsentrami-planeta-i-leto-menyaetsya-vladelets'],
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
