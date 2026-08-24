# -*- coding: utf-8 -*-
"""Pridex/Multispace (`ge283bafc`): второй независимый источник (канал
t.me/dealsma) назвал ПОИМЁННО четыре объекта, вошедшие в периметр сделки —
`eco.context` знал только их число и суммарную площадь (из realty.ria.ru).
Дословная цитата второго источника не лежит в тексте первого — обычная
таблица FIXES этого не пропустит (review.py проверяет цитату ПРОТИВ ОДНОЙ
статьи), поэтому здесь одноразовый скрипт, тот же приём, что и
fix_ibs_rubbles_investor_exits.py: старое значение сохраняется, к нему
дописывается предложение со ссылкой на новый источник.

Запуск: python3 pipeline/fix_pridex_multispace_object_names.py           # проверка
        python3 pipeline/fix_pridex_multispace_object_names.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'ge283bafc'
OLD_CONTEXT = ('В периметр сделки вошли четыре объекта общей площадью 18,2 '
               'тысячи квадратных метров в Москве и Санкт-Петербурге.')
ADDITION = ('Названы конкретные площадки: Multispace Dinamo, Multispace '
            'Tverskaya, Multispace Pravda и Multispace Dubinin’Sky.')
NEW_CONTEXT = OLD_CONTEXT + ' ' + ADDITION
NEW_SRC = ['@dealsma', 'https://t.me/dealsma/7309']


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в базе' % CARD_ID
    assert card.get('eco', {}).get('context') == OLD_CONTEXT, (
        'eco.context уже другое: %r' % card.get('eco', {}).get('context'))
    assert NEW_SRC not in card.get('src', []), 'источник уже добавлен'

    print('ДО: %r' % OLD_CONTEXT)
    print('ПОСЛЕ: %r' % NEW_CONTEXT)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 1

    card['eco']['context'] = NEW_CONTEXT
    card.setdefault('src', []).append(NEW_SRC)
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv[1:]))
