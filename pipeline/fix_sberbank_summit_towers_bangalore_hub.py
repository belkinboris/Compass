# -*- coding: utf-8 -*-
"""Сбербанк/Summit Towers (`g0ff8c5c4`): четвёртый черновик притока того
же дня (Коммерсантъ) повторяет уже известные факты один в один — то же
событие, тот же пресс-релиз банка, но добавляет одну деталь, которой не
было ни в одном из трёх уже привязанных источников: помимо 10 новых
филиалов в Индии Сбербанк планирует ещё и ИТ-хаб в Бангалоре (та же
цитата зампреда Анатолия Попова, июнь 2026).

Дополнение к уже занятому полю `eco.context` — не через review.py (та же
причина, что и у скрипта про филиалы: цитата покрывает всё предложение
целиком, а не только новую часть, добавленную поверх старого текста).
Пишет прямо в базу (карточка там же, где её оставил
`fix_sberbank_summit_towers_branches_plan.py`).

Запуск: python3 pipeline/fix_sberbank_summit_towers_bangalore_hub.py           # проверка
        python3 pipeline/fix_sberbank_summit_towers_bangalore_hub.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g0ff8c5c4'
OLD_TAIL = (
    'В июне зампред правления Сбербанка Анатолий Попов заявил, что банк '
    'планирует открыть 10 новых филиалов в Индии в дополнение к двум уже '
    'работающим офисам в Нью-Дели и Мумбаи.'
)
NEW_TAIL = (
    'В июне зампред правления Сбербанка Анатолий Попов заявил, что банк '
    'планирует открыть 10 новых филиалов в Индии в дополнение к двум уже '
    'работающим офисам в Нью-Дели и Мумбаи, а также IT-хаб в Бангалоре.'
)


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в базе' % CARD_ID
    context = card.get('eco', {}).get('context', '')
    assert context.endswith(OLD_TAIL), (
        'eco.context не заканчивается ожидаемым текстом: %r' % context[-160:])

    new_context = context[:-len(OLD_TAIL)] + NEW_TAIL
    print('БЫЛО (хвост): %r' % OLD_TAIL)
    print('СТАЛО (хвост): %r' % NEW_TAIL)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 1

    card['eco']['context'] = new_context
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv[1:]))
