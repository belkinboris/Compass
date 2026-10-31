# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка gb70f9719 (Lanit Ventures/
Colife): поле `date` несло «2024», хотя единственный источник карточки
(rb.ru) дословно датирован «28 февраля 2023, 20:29» — сделка объявлена в
конце февраля 2023 года, а не в 2024-м.

Не через review.py: `date_is_supported()` сознательно не переносит
сделку в другой год (см. CLAUDE.md) — перенос года решается отдельным
скриптом с явным assert на исходное состояние.
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gb70f9719'
OLD_DATE = '2024'
NEW_DATE = '2023'


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['date'] == OLD_DATE, f"date: неожиданное значение {deal['date']!r}"

    print(f"{CARD_ID} date: {OLD_DATE} -> {NEW_DATE} "
          "(источник rb.ru датирован 28 февраля 2023)")
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
