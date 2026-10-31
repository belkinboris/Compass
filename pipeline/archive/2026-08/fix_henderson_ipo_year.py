# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка gbfbab63c (Henderson
IPO): `date` стоял "2024" — но независимые источники (Ведомости,
02.11.2023: «Торги акциями группы начнутся сегодня, 2 ноября... Цена
IPO составила 675 руб. за акцию»; URL самой статьи датирован
2023/11/02) сходятся: IPO состоялось 2 НОЯБРЯ 2023 ГОДА. Все остальные
факты карточки (3,8 млрд ₽, тикер HNFG, ценовой диапазон) совпадают с
этой же сделкой — год в карточке просто неверен, это не другая сделка.

Не через review.py: `date_is_supported()` запрещает перенос ГОДА
(str(old)[:4] != new[:4] → отказ) — это уже задокументированная в
CLAUDE.md сознательная граница, а не недоработка.
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gbfbab63c'
OLD_DATE = '2024'
NEW_DATE = '2023-11-02'


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['date'] == OLD_DATE, f"date: неожиданное значение {deal['date']!r}"

    print(f"{CARD_ID} date: {OLD_DATE!r} -> {NEW_DATE!r} (IPO состоялось "
          "2 ноября 2023 года, Ведомости)")
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
