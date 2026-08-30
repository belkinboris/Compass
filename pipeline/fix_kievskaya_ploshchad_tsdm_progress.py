# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка g8ff9bdf8
(ГК «Киевская площадь» приобрела Центральный детский магазин на
Лубянке) — карточка не отражала судьбу здания после сделки и третью
оценку суммы. Проверено лично прямым WebFetch трёх источников.

1) `eco.context` (дополнено) — третья оценка суммы, тоже не согласующая
разброс. Дословно (Sostav.ru): «По оценке экспертов рынка, сумма сделки
могла составить около 15−20 млрд руб.» — третья, независимая от
Nikoliers (23-25 млрд) и IBC Real Estate (9-10 млрд) цифра, без
названного имени эксперта; разброс оценок НЕ сужается, а расширяется —
честно добавлена как ещё одна точка зрения, не как согласованная сумма.

2) `eco.context` (дополнено) — реконцепция 2025 года. Дословно
(Ведомости, 21.05.2025): «Расширение зоны гастрогалереи на нулевом
этаже, которая станет фудмоллом» с ростом числа точек «с 10–15 до около
30»; «Площадь фудмолла... в итоге займет 1700 кв. м, увеличится в
среднем на 1000 кв. м»; «Открытие запланировано на III квартал 2025 г.»
Новые арендаторы (Retail.ru, та же дата): «ресторан тайской кухни «Том
ям»... и мясной фастфуд-проект From». Объём инвестиций в реконцепцию НЕ
раскрыт: «планы по его модернизации, как и объем инвестиций в
преобразование нулевого этажа, пока не раскрываются» (Retail.ru).

НЕ ВКЛЮЧЕНО: точная согласованная сумма сделки — по-прежнему не
раскрыта ни одним источником («условия сделки не раскрыли» / «сумма не
разглашается» — Коммерсантъ, Ведомости, Forbes, Интерфакс); консультанты
и согласование ФАС — не найдены ни в одном из 7+ проверенных источников;
связь выручки «Галс-Девелопмент»/ВТБ с конкретными новыми проектами
(«Адмирал», «Монблан», БЦ «Север» и др.) — ни один источник не связывает
их напрямую с продажей именно ЦДМ, перенос был бы домыслом (Интерфакс
прямо: «В «Галс-Девелопмент» сделку не прокомментировали»).

Запуск: python3 pipeline/fix_kievskaya_ploshchad_tsdm_progress.py
        python3 pipeline/fix_kievskaya_ploshchad_tsdm_progress.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g8ff9bdf8'

OLD_CONTEXT = 'Окупаемость сделки, по мнению эксперта, составит не менее 12–15 лет.'
NEW_CONTEXT = OLD_CONTEXT + (
    ' Третья, отдельная от Nikoliers и IBC Real Estate оценка (Sostav.ru): '
    '«По оценке экспертов рынка, сумма сделки могла составить около '
    '15−20 млрд руб.» — разброс оценок этим не сужается. В мае 2025 '
    'года начата реконцепция: «Расширение зоны гастрогалереи на нулевом '
    'этаже, которая станет фудмоллом» с ростом числа точек с 10–15 до '
    'около 30, площадью 1700 кв. м; открытие запланировано на III '
    'квартал 2025 года; новые арендаторы — ресторан «Том ям» и '
    'фастфуд-проект From (Ведомости, Retail.ru). Объём инвестиций в '
    'реконцепцию не раскрыт.'
)

NEW_SRC = [
    ['Sostav.ru', 'https://www.sostav.ru/publication/gk-kievskaya-ploshchad-kupila-tsentralnyj-detskij-magazin-na-lubyanke-67207.html'],
    ['Ведомости', 'https://www.vedomosti.ru/business/articles/2025/05/21/1111498-kievskaya-ploschad-menyaet-kontseptsiyu-tsdm-na-lubyanke'],
    ['Retail.ru', 'https://www.retail.ru/news/kievskaya-ploshchad-rekontseptiruet-tsdm-na-lubyanke-21-maya-2025-264814/'],
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
    print('\n=== src добавится ===')
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
