# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
g5b65aad0 (Henderson выкупил бывший флагманский магазин Massimo Dutti
на Кузнецком мосту) — заявленные планы реализованы: флагманский салон
открылся.

Проверено лично прямым WebFetch (CRE.ru, 30.05.2023): «Площадь салона
составила около 1000 кв. м», здание «построено еще в 1882 г. по
проекту Александра Каминского» (семейного архитектора братьев
Третьяковых), открытие — в мае 2023 года.

НЕ ВКЛЮЧЕНО: финансовые показатели именно этого салона — ни один
источник их не приводит отдельно от показателей всей компании;
дальнейшая экспансия Henderson в премиальную недвижимость — по данным
саб-агента, новых покупок зданий под флагманские магазины в 2023-2026
годах не нашлось (собственный распредцентр под Шереметьевом — склад,
не магазин, построен на средства IPO).

Запуск: python3 pipeline/fix_henderson_kuznetsky_flagship_opened.py
        python3 pipeline/fix_henderson_kuznetsky_flagship_opened.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g5b65aad0'

OLD_EXTRA = (
    'Сделка купли-продажи недвижимости между Henderson (покупатель) и '
    'Айсель Трудел (продавец). Henderson планирует открыть в этом '
    'особняке флагманский магазин.'
)
NEW_EXTRA = OLD_EXTRA + (
    ' Флагманский салон открылся в мае 2023 года — занял два этажа '
    'здания площадью около 1000 кв. м, построенного в 1882 году по '
    'проекту Александра Каминского, семейного архитектора братьев '
    'Третьяковых.'
)

NEW_SRC = [
    ['CRE.ru', 'https://cre.ru/news/91064'],
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
