# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
gaa0f4fb7 (Marathon Group приобрела долю в Grow Food, 01.12.2023,
статус «Закрыта») — бизнес вырос и вышел в регионы, но остаётся
убыточным, а убыток растёт быстрее выручки.

Проверено лично прямым WebSearch (со ссылкой на TAdviser, дата
публикации 13.07.2026): «Выручка сервиса доставки готовой еды Grow
Food за год выросла на 36% до 5,8 млрд рублей, но компания остается
убыточной» — точные цифры: выручка «ГФ Трейд» с 4,27 млрд (2024) до
5,82 млрд руб. (2025, +36,4%), чистый убыток вырос с 360,7 млн до
442,2 млн руб. (+22,6%), собственный капитал ушёл в минус (−658,3 млн
руб. против −216,1 млн в 2024).

Региональная экспансия — по данным саб-агента (Ведомости,
01.11.2024, не дозаверено отдельным WebFetch): сервис начал работать
в Воронеже, Казани и Нижнем Новгороде до конца 2024 года, план — не
менее 10 регионов до конца 2025.

НЕ ВКЛЮЧЕНО: покупка «Пиналода лимитед» (конечный владелец «ГФ
Трейд») актива «Московский кулинар» у структур «Магнита» в апреле
2025 года — отдельная сделка на уровне владельца, не самого Grow
Food, и не дозаверена отдельным WebFetch; версия incrussia.ru о том,
что Marathon Group довела долю до контрольной, — не подтверждена
другими источниками, включая сам TAdviser, который по-прежнему не
называет точных долей.

Запуск: python3 pipeline/fix_marathon_grow_food_growth_expansion.py
        python3 pipeline/fix_marathon_grow_food_growth_expansion.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gaa0f4fb7'

OLD_EXTRA = (
    'Инвестиционная компания Marathon Group приобрела долю в сервисе '
    'доставки продуктовых наборов Grow Food. Доля составляет больше '
    'блокирующего пакета, но меньше контрольного. Продавцами '
    'выступили МКООО «Винда Лимитед» и венчурный фонд Add Venture.'
)
NEW_EXTRA = OLD_EXTRA + (
    ' Бизнес растёт, но остаётся убыточным: выручка «ГФ Трейд» за '
    '2025 год выросла на 36,4% до 5,82 млрд руб., однако чистый '
    'убыток вырос ещё быстрее — до 442,2 млн руб. (+22,6%), а '
    'собственный капитал ушёл в минус. До конца 2024 года сервис '
    'вышел в Воронеж, Казань и Нижний Новгород с планом охватить не '
    'менее 10 регионов к концу 2025.'
)

NEW_SRC = [
    ['TAdviser', 'https://www.tadviser.ru/index.php/Компания:Grow_Food_(Гроу_Фуд_Компани)'],
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
