# -*- coding: utf-8 -*-
"""Карточка g39cb44b9 («Владимир Седов выкупил 73% акций «Асконы» у
Hilding Anders») несла отрасль «Пищепром и напитки» — механическая
ошибка компактного импорта. «Аскона» производит мебель и товары для сна
(матрасы), а не продукты питания; уже привязанный источник (Коммерсантъ)
прямо называет её «Производитель мебели и товаров для сна». В словаре
отраслей платформы нет отдельной категории для мебели (только одна
затронутая карточка — заводить новую отрасль ради неё не стоит, тот же
принцип, что уже применён к «Производству тары»: там было 12+ карточек,
здесь одна), поэтому используется ближайшая существующая — «Потребительские
товары» (та же категория, что у производителей бытовых приборов).

Единственный найденный кандидат: полнотекстовый поиск по базе на слова
«Аскона»/«матрас» не нашёл других карточек с той же ошибкой — дефект
единичный, не систематический.

Источник — читал напрямую (fetch_article_texts.py, закэширован):
https://www.kommersant.ru/doc/7958520

Запуск: python3 pipeline/fix_askona_industry_misclassification.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g39cb44b9'
OLD_IND = 'Пищепром и напитки'
NEW_IND = 'Потребительские товары'


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['ind'] == OLD_IND, f"ind: неожиданное значение {deal['ind']!r}"

    print(f"{CARD_ID} ind: {OLD_IND!r} -> {NEW_IND!r} "
          f"(«Аскона» — производитель мебели и товаров для сна, не пищепром)")
    deal['ind'] = NEW_IND

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО")
    else:
        print("Сухой прогон. Запись — с --write.")


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
