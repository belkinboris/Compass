# -*- coding: utf-8 -*-
"""Месячная очередь, карточка g2632677b (Юнифрост/группа «Меридиан»):
дельта-поиск нашёл независимую оценку сделки — заметно ниже диапазона
BGP Capital, который уже был единственным в eco.val. Не через review.py:
поле уже несёт содержание (перефразированное относительно источника —
«Стоимость сделки может превысить 5 млрд руб.» вместо дословной цитаты
Ивана Пешкова), не образует непрерывный кусок текста со вторым,
независимым источником.

Источник — читал напрямую (fetch_article_texts.py, закэширован):
https://agroexpert.press/all-events/postavshhik-ryboprodukczii-yunifrost-pokupaet-proizvoditelya-preservov-meridian/
Дословная цитата: «Управляющий партнер Agro & Food Communication Илья
Березнюк считает, что стоимость сделки будет чуть меньше — 1,5–4,5 млрд
рублей.»

Запуск: python3 pipeline/fix_unifrost_meridian_valuation_context.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g2632677b'

OLD_VAL = 'Стоимость сделки может превысить 5 млрд руб.'
ADDITION = (
    'Управляющий партнер Agro & Food Communication Илья Березнюк '
    'оценивает стоимость сделки ниже — в 1,5–4,5 млрд рублей.'
)
NEW_VAL = OLD_VAL + ' ' + ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['val'] == OLD_VAL, \
        f"eco.val: неожиданное значение {deal['eco']['val']!r}"

    print(f"{CARD_ID} eco.val: += независимая оценка Ильи Березнюка "
          f"(Agro & Food Communication), ниже диапазона BGP Capital")
    deal['eco']['val'] = NEW_VAL

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО")
    else:
        print("Сухой прогон. Запись — с --write.")


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
