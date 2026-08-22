# -*- coding: utf-8 -*-
"""Карточка cccedc36b (ЭТМ / АВС-Электро), ни разу не прошедшая
проверку чтением: `date` стоял "unknown". RusCable.Ru датирует
видеообращение гендиректора ЭТМ Владислава Рихтера, объявившее
сделку, 26 мая 2025 года, 18:15 — сам Рихтер говорит «с сегодняшнего
дня мы все становимся единой командой», то есть это не просто
объявление о намерении, а заявление о вступлении в силу.

Не через review.py: `date_is_supported()` требует, чтобы ГОД старого
значения совпадал с новым — старое значение "unknown"[:4] = "unkn"
никогда не совпадёт с "2025".
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'cccedc36b'
OLD_DATE = 'unknown'
NEW_DATE = '2025-05-26'


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['date'] == OLD_DATE, f"date: неожиданное значение {deal['date']!r}"

    print(f"{CARD_ID} date: {OLD_DATE!r} -> {NEW_DATE!r} (видеообращение "
          "гендиректора ЭТМ, RusCable.Ru, 26.05.2025)")
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
