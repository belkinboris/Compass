# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g62ea52ce (Capital Group/
универмаг «Московско-Орловский»): в карточке стоял только год «2023»,
хотя первоисточник (Consul Group, тот же, на который опирался @dealsma)
даёт точные даты: договор мены заключён 9 декабря 2024 года, сделка
завершена 18 декабря 2024 года. Год расходится, поэтому не через
review.py — он структурно отказывает в смене года (см. CLAUDE.md).

Источник: https://t.me/s/expertsconsulgroup/616 — читал напрямую.
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g62ea52ce'
OLD_DATE = '2023'
NEW_DATE = '2024-12-18'


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['date'] == OLD_DATE, \
        f"date: неожиданное значение {deal['date']!r}"

    print(f"{CARD_ID} date: '{OLD_DATE}' -> '{NEW_DATE}' (сделка "
          "завершена 18 декабря 2024, а не в 2023 году)")
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
