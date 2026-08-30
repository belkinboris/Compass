# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
gc3452fa6 (Газпромбанк инвестировал в сеть фитнес-клубов DDX Fitness) —
сеть выросла в 2,5 раза после сделки, а финансовые показатели впервые
раскрыты в проспекте облигаций 2026 года. Проверено лично прямым
WebFetch двух источников.

`eco.context` (дополнено). Дословно (Retail.ru, 11.08.2026): «Двухэтажный
клуб площадью 1 767 кв. м стал юбилейной 170-й точкой сети» — рост с 69
клубов на момент сделки (январь 2024) до 170 к августу 2026.

`eco.target_fin` (дополнено). Дословно (Smart-lab.ru, 03.03.2026, разбор
выпуска облигаций ИЛОН-001Р-01): «Выручка выросла на 88% до 9,6 млрд
руб.», «Чистая прибыль подскочила почти в 3 раза до 1,2 млрд руб.»,
«EBITDA margin удерживается на уровне 38%» — первые публично раскрытые
показатели компании (в момент сделки в 2024 году финансы предмета были
прочерком).

НЕ ВКЛЮЧЕНО: показатели за 2025 год — расходятся между источниками
(оценка FitnessData «16 млрд руб.» против других агрегаторских обзоров
облигаций, называющих иную цифру) и не привязаны к отчётности самой
компании, а к сторонней оценке; отношение чистый долг/EBITDA (1,3–1,5х)
— не факт о СДЕЛКЕ или её предмете напрямую, а параметр выпуска
облигаций, решено не перегружать карточку; рост доли Газпромбанка выше
11,1% и консультанты сделки — не нашлись ни в одном источнике.

Запуск: python3 pipeline/fix_ddx_fitness_growth_and_financials.py
        python3 pipeline/fix_ddx_fitness_growth_and_financials.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gc3452fa6'

OLD_CONTEXT = (
    'DDX Fitness существует с 2018 года. В 2019 году в число ее учредителей '
    'вошли Иван Ситников — партнер экс-супруги главы «Роснефти» Игоря '
    'Сечина Марины Сечиной, а также основатели Росевробанка (в конце 2018 '
    'года объединился с Совкомбанком) Илья Бродский и Андрей Суздальцев '
    '(см. «Ъ» от 24 апреля 2019 года). На сайте сети значатся 69 '
    'существующих и готовящихся к открытию клубов.'
)
NEW_CONTEXT = OLD_CONTEXT + (
    ' К августу 2026 года сеть выросла до 170 клубов: «Двухэтажный клуб '
    'площадью 1 767 кв. м стал юбилейной 170-й точкой сети» (Retail.ru, '
    '11 августа 2026).'
)

OLD_TARGET_FIN = (
    'Президент Ассоциации операторов фитнес-индустрии Ольга Киселева '
    'говорит, что DDX Fitness входит в десятку игроков, занимая около 15% '
    'московского рынка.'
)
NEW_TARGET_FIN = OLD_TARGET_FIN + (
    ' В проспекте облигаций 2026 года впервые раскрыты финансовые '
    'показатели: выручка выросла на 88% до 9,6 млрд ₽, чистая прибыль '
    'подскочила почти в 3 раза до 1,2 млрд ₽, EBITDA margin удерживается '
    'на уровне 38% (Smart-lab.ru, 3 марта 2026).'
)

NEW_SRC = [
    ['Retail.ru', 'https://www.retail.ru/news/set-ddx-fitness-otkryla-170-y-klub-v-zhk-v-koroleve-11-avgusta-2026-280922/'],
    ['Smart-lab.ru', 'https://smart-lab.ru/blog/1272233.php'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_CONTEXT
    assert deal['eco']['target_fin'] == OLD_TARGET_FIN
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('\n=== eco.target_fin: станет ===')
    print(NEW_TARGET_FIN)
    print('\n=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        deal['eco']['target_fin'] = NEW_TARGET_FIN
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
