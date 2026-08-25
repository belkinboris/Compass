# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g5ccd2edb (Роман Володин
выкупил у основателей компанию АТОЛ, декабрь 2024): дельта-поиск нашёл, что
Александр Бочков, занявший пост гендиректора холдинга 13 ноября 2024 года,
руководил им лишь около двух месяцев — 22 января 2025 года гендиректором
ООО «УК «АТОЛ»» вновь стал сам новый собственник Роман Володин (ЕГРЮЛ,
audit-it.ru), и минимум по апрель 2026 он публично фигурирует как
действующий CEO АТОЛ (Коммерсантъ, Cleverence). Добавлена выручка/прибыль
операционного юрлица ООО «АТОЛ» за 2025 год по РСБУ — с явной пометкой
периметра, поскольку в прессе гуляют более крупные, несопоставимые цифры
(вероятно, вся группа юрлиц или брендовая PR-цифра, а не одно юрлицо по
РСБУ; ни одна из них не проверена дословной цитатой из первички). Не через
review.py: цитаты из НОВЫХ источников (audit-it.ru/ЕГРЮЛ, Коммерсантъ) в
поле, уже содержащем текст из другого источника.

Запуск: python3 pipeline/fix_atol_volodin_ceo_return_context.py
        python3 pipeline/fix_atol_volodin_ceo_return_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g5ccd2edb'

OLD_CONTEXT = (
    'Компания АТОЛ была основана в 2001 году Алексеем и Ириной '
    'Макаровыми, которые, согласно данным СПАРК, владели по 50% бизнеса.'
)
CONTEXT_ADDITION = (
    ' Александр Бочков, занявший пост гендиректора холдинга 13 ноября '
    '2024 года, руководил им лишь около двух месяцев: 22 января 2025 '
    'года гендиректором ООО «УК «АТОЛ»» вновь стал сам новый собственник '
    'Роман Володин (данные ЕГРЮЛ) — и минимум по апрель 2026 года '
    'публично фигурирует как действующий CEO АТОЛ. По официальной '
    'отчётности РСБУ операционного юрлица ООО «АТОЛ» (не всей группы), '
    'выручка за 2025 год составила 6,7 млрд руб. (снижение на 6,7% к '
    '2024 году), чистая прибыль — 429 млн руб. (рост на 60,1%).'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['audit-it.ru', 'https://www.audit-it.ru/contragent/1097746549966_ooo-uk-atol'],
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/8587872'],
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
