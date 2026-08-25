# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g5b4a3bf8 (ГК «Таврос»
приобрела United buns): дельта-поиск разрешил, чем закончилась
промежуточная структура владения (АО «Виннер»/«Линия успеха»/«Шаг
вперёд» + Шутилин, январь 2025, бенефициары скрыты) — в конце мая 2025
года 100% долей ООО «Гипфель» консолидировано на ООО «Багерстат Рус»,
уже действующем производстве «Тавроса». Сумма и этого шага не
раскрыта. Бренд United buns продолжает использоваться отдельно от
«Багерстат», признаков ребрендинга или закрытия не найдено. Не через
review.py: цитаты из ДВУХ новых источников (shoppers.media, new-retail.ru)
в поле, уже содержащем текст из других источников.

Запуск: python3 pipeline/fix_tavros_united_buns_final_structure.py
        python3 pipeline/fix_tavros_united_buns_final_structure.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g5b4a3bf8'

OLD_CONTEXT = (
    'Ресторатор Александр Колобов вышел из числа учредителей ООО '
    '«Гипфель», где ранее ему принадлежало 90%, следует из ЕГРЮЛ. '
    'Сейчас учредителями компании выступают АО «Виннер» (доля в '
    'уставном капитале 33%), АО «Линия успеха» (33%), АО «Шаг вперед» '
    '(33%) и Андрей Шутилин (1%), пишет «Коммерсант». Бенефициары новых '
    'компаний-учредителей «Гипфель» скрыты. Но АО «Виннер» недавно '
    'стало совладельцем МПК «Тосненский», долю в котором приобрел '
    'агрохолдинг «Таврос». В сделке участвовал и господин Шутилин. '
    'Ранее он владел 25% в ООО НТ, которое с конца 2023 года входит в '
    'ООО «УК "Таврос"».'
)
CONTEXT_ADDITION = (
    ' В конце мая 2025 года промежуточная структура владения '
    'разрешилась: 100% долей ООО «Гипфель» перешло к ООО «Багерстат '
    'Рус» — уже действующему производству булочек «Тавроса» (куплено у '
    'Lantmännen Unibake осенью 2023 года). Сумма этого шага также не '
    'раскрывалась. Бренд United buns продолжает использоваться '
    'отдельно; признаков объединения с брендом «Багерстат» или его '
    'закрытия не найдено. Выручка «Гипфеля» за 2024 год составила 2,8 '
    'млрд руб., чистая прибыль — 571 млн руб.'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['shoppers.media', 'https://shoppers.media/news/23072_struktura-tavrosa-stala-vladelcem-proizvoditelia-bulok-united-buns'],
    ['new-retail.ru', 'https://new-retail.ru/novosti/retail/tavros_stal_vladeltsem_proizvoditelya_bulok_dlya_burger_king/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
