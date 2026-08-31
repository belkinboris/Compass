# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка gdb854428
(Сбербанк инвестиции приобрёл логистический склад «Пивдома») — три пустых
поля «Экономиста» (`eco.val`, `eco.target_fin`) и расширение `eco.rationale`
экономической логикой сделки, которой в карточке не было.

Рыночная оценка склада — проверено лично прямым WebFetch (Retail.ru,
24 октября 2024 года): «Эксперты оценивают рыночную стоимость склада на
Липкинском шоссе в 6–6,5 млрд руб.» — это независимая оценка, отличная
от цены ПРОШЛОЙ продажи того же объекта (4,64 млрд ₽ в 2021 году), уже
стоящей в `eco.context`; в `eco.val` её не было вовсе.

Финансовые показатели цели (ООО «СДМ ТК-2», ИНН 9701161771) за 2024 год —
проверено лично прямым WebFetch (страница компании на РБК Компании):
выручка 948 684 000 ₽, чистый убыток 374 789 000 ₽. Убыток при владении
одним складским активом ожидаем (амортизация, проценты по обслуживанию
долга при покупке) и не противоречит инвестиционной логике сделки.

Экономическая логика сделки — проверено лично прямым WebFetch
(ibcrealestate.ru, 24 октября 2024 года, цитата члена совета директоров
IBC Real Estate Микаэла Казаряна): «Стратегия финансовой организации
подразумевает покупку акций и долей компаний, владеющих качественными
активами в расчете на рост акционерной стоимости и последующую продажу
объектов» — это НЕ дублирует уже стоящую в `eco.rationale` цитату
представителя Сбербанка (та — про ЭТУ конкретную сделку и планы на
операционного партнёра), а объясняет общую стратегию покупателя, и
добавлена вторым предложением того же поля.

НЕ ВКЛЮЧЕНО: поиск операционного партнёра для управления объектом (о
котором Сбербанк заявлял на момент сделки) — свежих новостей о том, кто
им стал, не нашлось; повторная сделка того же покупателя ("Сбербанк
инвестиции") на другом складе в декабре 2025 года — это ДРУГОЙ фонд,
связанный со Сбербанком, и к этой карточке не относится (не смешивать).

Запуск: python3 pipeline/fix_pivdom_valuation_and_target_fin.py
        python3 pipeline/fix_pivdom_valuation_and_target_fin.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gdb854428'

OLD_VAL = '—'
NEW_VAL = (
    'Эксперты оценивают рыночную стоимость склада на Липкинском шоссе '
    'в 6–6,5 млрд руб. (Retail.ru, 24 октября 2024 года) — это выше '
    'цены его прошлой продажи (4,64 млрд ₽ в 2021 году, см. «Контекст»).'
)

OLD_TARGET_FIN = '—'
NEW_TARGET_FIN = (
    'ООО «СДМ ТК-2» (владелец склада) за 2024 год показало выручку '
    '948,68 млн ₽ и чистый убыток 374,79 млн ₽ (данные РБК Компании).'
)

OLD_RATIONALE = (
    'Представитель Сбербанка уточнил, что данный актив приобретен в '
    'инвестиционных целях. По его словам, на следующем этапе финансовая '
    'организация планирует привлечь партнера, который будет заниматься '
    'операционным управлением объектом.'
)
NEW_RATIONALE = OLD_RATIONALE + (
    ' Стратегия покупателя системная, а не разовая: «Стратегия '
    'финансовой организации подразумевает покупку акций и долей '
    'компаний, владеющих качественными активами в расчете на рост '
    'акционерной стоимости и последующую продажу объектов» (Микаэл '
    'Казарян, член совета директоров IBC Real Estate, ibcrealestate.ru, '
    '24 октября 2024 года).'
)

NEW_SRC = [
    ['Retail.ru', 'https://www.retail.ru/news/struktura-sberbanka-stala-vladeltsem-byvshego-logoparka-pivdoma-v-moskovskoy-obl-24-oktyabrya-2024-246620/'],
    ['IBC Real Estate', 'https://ibcrealestate.ru/news/sberbank-investitsii-stal-vladeltsem-sdm-tk-2/'],
    ['РБК Компании', 'https://companies.rbc.ru/id/1207700323511-obschestvo-s-ogranichennoj-otvetstvennostyu-sdm-tk-2/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['val'] == OLD_VAL
    assert deal['eco']['target_fin'] == OLD_TARGET_FIN
    assert deal['eco']['rationale'] == OLD_RATIONALE

    new_src = deal['src'] + NEW_SRC

    print('=== eco.val: станет ===')
    print(NEW_VAL)
    print('\n=== eco.target_fin: станет ===')
    print(NEW_TARGET_FIN)
    print('\n=== eco.rationale: станет ===')
    print(NEW_RATIONALE)
    print('\n=== src: добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['val'] = NEW_VAL
        deal['eco']['target_fin'] = NEW_TARGET_FIN
        deal['eco']['rationale'] = NEW_RATIONALE
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
