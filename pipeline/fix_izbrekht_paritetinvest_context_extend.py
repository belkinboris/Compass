# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g473685f6 (Денис Избрехт
увеличил долю в ООО «Паритетинвест» до 73,35%): единственный источник в
базе был Telegram-канал @dealsma, без точной даты. Дельта-поиск нашёл
точную дату (14 апреля 2025 года, по выписке ЕГРЮЛ, день перед статьёй
Коммерсанта) и полную историю смены долей за 2024-2025 годы. Не через
review.py: точная дата и хронология — из ДВУХ новых источников
(kommersant.ru, abireg.ru), комбинируемых с уже записанным текстом.

Запуск: python3 pipeline/fix_izbrekht_paritetinvest_context_extend.py
        python3 pipeline/fix_izbrekht_paritetinvest_context_extend.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g473685f6'

OLD_DATE = '2025'
NEW_DATE = '2025-04-14'

OLD_CONTEXT = (
    'В апреле 2025 года Денис Избрехт стал основным владельцем '
    'белгородской агрофирмы ООО «Паритетинвест», которая ранее была '
    'поделена между Михаилом Тебекиным, сыном попавшего под уголовное '
    'дело бизнесмена Владимира Тебекина, и Ириной Кладовой.'
)
CONTEXT_ADDITION = (
    ' Изначально в компании было два владельца — по 50% у Тебекина и '
    'Кладовой; в конце ноября 2024 года Тебекин передал Избрехту 5% '
    'своей доли (причина официально не раскрывалась). К концу 2024 года '
    'Избрехту уже принадлежало 49%, а Тебекину — только 1%. В марте 2025 '
    'года Кладовая вышла из состава учредителей, её 50% были '
    'распределены между Избрехтом и самим обществом (25,65%).'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['kommersant.ru', 'https://www.kommersant.ru/doc/7657872'],
    ['abireg.ru', 'https://abireg.ru/newsitem/106622/'],
    ['abireg.ru', 'https://abireg.ru/newsitem/105186/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['date'] == OLD_DATE
    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== date ===', NEW_DATE)
    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['date'] = NEW_DATE
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
