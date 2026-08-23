# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g3875e8f5 (Capital
Group/ТВК «Тишинка»): дельта-поиск нашёл, ПОЧЕМУ не состоялась
предыдущая попытка продажи Element Development, которую карточка уже
упоминала одной строкой без подробностей, — и назвал трёх совладельцев
объекта вместо одного.

Источник: Ведомости, 29 апреля 2025 (иск) и 28 октября 2025 (решение
суда) — оба читал напрямую.
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g3875e8f5'
OLD_CONTEXT = (
    'В прошлом году собственники «Тишинки» уже договорились о продаже '
    'комплекса с петербургским девелопером Element Development (сейчас '
    'Element), однако сделка не состоялась.'
)
ADDITION = (
    'Владимир Земцов, Елена Козина и Сергей Травин, которым принадлежат '
    'права на комплекс, подавали иск к структуре Element Development, '
    'принуждая её заключить договор купли-продажи, — но в октябре 2025 '
    'года Арбитражный суд Москвы отказался удовлетворить иск. По словам '
    'представителя Element, спор возник из-за невыполнения продавцами '
    '«Тишинки» обязательных условий сделки, в том числе погашения '
    'ипотеки по одному из зданий комплекса.'
)
NEW_CONTEXT = OLD_CONTEXT + ' ' + ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"

    print(f"{CARD_ID} eco.context: += иск и решение суда по несостояв"
          "шейся сделке с Element Development")
    deal['eco']['context'] = NEW_CONTEXT

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО")
    else:
        print("Сухой прогон. Запись — с --write.")


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
