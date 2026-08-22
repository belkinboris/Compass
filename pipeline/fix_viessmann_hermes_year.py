# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g04efcb3a (Viessmann/
«Гермес-Урал»): поле `date` несло «2024», хотя все проверенные источники
сходятся на апреле 2023 года.

Коммерсантъ-Воронеж (doc/5953464, дата публикации «25.04.2023»): «Сделка
была завершена 19 апреля» — то есть 19 апреля 2023 года. Независимо
подтверждено: abireg.ru (25.04.2023) — «Пока смена собственника не
отражена в юридических документах» (только что завершившаяся сделка);
переименование обеих «дочек» в ООО «Гермес»/«Гермес-Липецк» датировано
06.06.2023 (c-o-k.ru) — на полтора месяца позже закрытия, что логично
только при годе сделки 2023, а не 2024.

Не через review.py: перенос сделки в другой год review.py сознательно
не делает (см. CLAUDE.md) — решается отдельным скриптом с явным assert
на исходное состояние.
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g04efcb3a'
OLD_DATE = '2024'
NEW_DATE = '2023'


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['date'] == OLD_DATE, f"date: неожиданное значение {deal['date']!r}"

    print(f"{CARD_ID} date: {OLD_DATE} -> {NEW_DATE} "
          "(сделка завершена 19 апреля 2023, Коммерсантъ-Воронеж)")
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
