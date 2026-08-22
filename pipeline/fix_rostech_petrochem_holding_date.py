# -*- coding: utf-8 -*-
"""Карточка cfdb3878d («Ростех» / нефтехимический холдинг), ни разу не
прошедшая проверку чтением: `date` стоял "unknown". Первоисточник
карточки (AK&M, `src`) датирован точно: «AK&M 18 мая 2023 14:26» —
подтверждено независимо (ura.news, тот же новостной цикл, со ссылкой
на «Известия»).

Не через review.py: "unknown" не в формате ГГГГ-ММ-ДД,
`date_is_supported()` откажет на несовпадении года.

Проверено и НЕ перенесено (недостаточно подтверждено): найденные при
дельта-поиске утверждения о согласовании наблюдательным советом
«Ростеха» и о числе «13 предприятий „Росхимзащиты“» — при прямой
проверке текста ura.news эти детали в нём не обнаружены (в отличие от
даты и общего числа «не менее 15 предприятий», которые совпадают
дословно); переносить неподтверждённое в карточку не стал.
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'cfdb3878d'
OLD_DATE = 'unknown'
NEW_DATE = '2023-05-18'


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['date'] == OLD_DATE, f"date: неожиданное значение {deal['date']!r}"

    print(f"{CARD_ID} date: {OLD_DATE!r} -> {NEW_DATE!r} (AK&M, "
          "подтверждено ura.news)")
    deal['date'] = NEW_DATE

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО")
    else:
        print("Сухой прогон. Запись — с --write.")


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
