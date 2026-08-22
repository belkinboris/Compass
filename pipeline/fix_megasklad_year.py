# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка gfbf1350d (Rein Capital/
«Мегасклад»): поле `date` несло только год «2024». Дельта нашла пять
независимых источников (Ведомости, TAdviser, Logirus, Constructorium,
vc.ru), сходящихся на том, что этот раунд (более 200 млн ₽, 35% в
капитале) был закрыт в НОЯБРЕ 2025 года, а не в 2024-м — Ведомости прямо
пишут «В ноябре 2025 г. Rein Capital уже вложила в компанию 200 млн
руб.» (сумма совпадает с суммой карточки дословно). Точный день ноября
ни один источник не называет — оставлен только год (тот же принцип, что
уже применён к датам-заглушкам: месяц без дня в поле `date` не пишется,
год без дня — можно).

Не через review.py: перенос сделки в ДРУГОЙ год `review.py` не делает
никогда (сознательная граница `date_is_supported()` — см. CLAUDE.md,
«review.py не умеет переносить сделку в другой год — и не должен»).
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gfbf1350d'
OLD_DATE = '2024'
NEW_DATE = '2025'


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['date'] == OLD_DATE, \
        f"date: неожиданное значение {deal['date']!r}"

    print(f"{CARD_ID} date: {OLD_DATE!r} -> {NEW_DATE!r} (пять "
          "источников независимо называют ноябрь 2025, не 2024)")
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
