# -*- coding: utf-8 -*-
"""Карточка cc108d4d8 (Gunvor / LUKOIL International GmbH), ни разу не
прошедшая проверку чтением: `date` стоял "unknown". Пресс-релиз LUKOIL
и синхронная публикация Ведомостей называют точную дату предложения —
30 октября 2025 года («"Лукойл" сообщил о получении соответствующего
предложения от Gunvor 30 октября», vedomosti.ru/business/articles/
2025/11/08/1153105-kak-lukoil-mozhet).

Не через review.py: `date_is_supported()` требует, чтобы `new` был в
формате ГГГГ-ММ-ДД и чтобы ГОД старого значения совпадал с новым —
старое значение "unknown"[:4] = "unkn" никогда не совпадёт с "2025".
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'cc108d4d8'
OLD_DATE = 'unknown'
NEW_DATE = '2025-10-30'


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['date'] == OLD_DATE, f"date: неожиданное значение {deal['date']!r}"

    print(f"{CARD_ID} date: {OLD_DATE!r} -> {NEW_DATE!r} (дата предложения "
          "Gunvor, LUKOIL press release + Ведомости)")
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
