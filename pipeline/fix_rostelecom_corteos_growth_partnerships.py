# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
g8952793b (Ростелеком приобрел 60% акций платформы Кортеос,
19.12.2023, статус «Закрыта») — структура владения не изменилась, но
платформа выросла и обзавелась партнёрствами внутри экосистемы
«Ростелекома».

Партнёрство с Continent Express — проверено лично прямым WebFetch
(company.rt.ru, 24.12.2024): «Continent Express стала первым
лицензированным партнером-интегратором компании «Кортеос»»,
«Стратегическое партнерство с «Ростелекомом» позволило «Кортеос»
расширить технологические возможности платформы за счет предоставления
разработчикам и интеграторам лицензии с открытым кодом».

НЕ ВКЛЮЧЕНО: финансовые показатели «Кортеос» за 2024-2025 годы и
партнёрство с ORS (октябрь 2025) — по данным саб-агента только из
агрегаторов/CNews, не дозаверены отдельным WebFetch в этом заходе;
покупка Ростелекомом 49% ООО «Эртек» (январь 2026) — саб-агент прямо
указал, что это ДРУГАЯ, не связанная с «Кортеос» сделка, в карточку не
добавляется; увеличение доли Ростелекома в самом «Кортеос» до 100% —
саб-агент не нашёл, состав учредителей с декабря 2023 года не менялся.

Запуск: python3 pipeline/fix_rostelecom_corteos_growth_partnerships.py
        python3 pipeline/fix_rostelecom_corteos_growth_partnerships.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g8952793b'

OLD_EXTRA = (
    'Ростелеком приобрел 60% акций ООО «Кортеос» — разработчика '
    'платформы Corteos Platform для автоматизации делового туризма и '
    'управления корпоративными поездками. Основатели компании '
    'сохранили свои доли. Платформа обрабатывает более 7,5 тыс. '
    'деловых поездок в день.'
)
NEW_EXTRA = OLD_EXTRA + (
    ' В декабре 2024 года Continent Express стала первым '
    'лицензированным партнёром-интегратором «Кортеос» — партнёрство '
    'дало сторонним разработчикам открытый доступ к платформе для '
    'кастомизированных решений корпоративным клиентам. Структура '
    'владения не изменилась: доли основателей и Ростелекома те же, '
    'что на момент сделки.'
)

NEW_SRC = [
    ['Ростелеком', 'https://www.company.rt.ru/press/news/d472111/'],
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
