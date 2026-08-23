# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g4803e120 (продажа сети
«Инвитро»): дельта-поиск нашёл ТРЕТЬЮ, заметно более низкую экспертную
оценку стоимости сделки — 12–15 млрд руб. (в 2-3 раза меньше двух уже
записанных оценок в 30-40 млрд руб.). Разброс оценок сам по себе
показателен и стоит того, чтобы его видел читатель.

Источник: Коммерсантъ (doc/6112194) — читал напрямую. Не через
review.py: третья цифра из ТОГО ЖЕ источника, но другого предложения,
не идущего подряд с уже внесённой цитатой.
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g4803e120'
OLD_VAL = (
    'Сумма сделки неизвестна. Она может превышать 40 млрд руб., '
    'считает генеральный директор «Infoline-аналитики» Михаил '
    'Бурмистров. Однако генеральный директор DSM Group Сергей Шуляк '
    'предполагает, что стороны могли договориться и на 30 млрд руб.'
)
ADDITION = (
    'Управляющий директор Peregrine Capital Дмитрий Габышев оценил '
    'стоимость «Инвитро» ниже — в 12–15 млрд руб., или 5–6 EBITDA за '
    '2022 год.'
)
NEW_VAL = OLD_VAL + ' ' + ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['val'] == OLD_VAL, \
        f"eco.val: неожиданное значение {deal['eco']['val']!r}"

    print(f"{CARD_ID} eco.val: += третья, более низкая оценка "
          "(Peregrine Capital, 12-15 млрд ₽)")
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
