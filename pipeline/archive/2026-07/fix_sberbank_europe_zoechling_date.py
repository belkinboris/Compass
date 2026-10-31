# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g5c3eeb06 (Сбербанк/
Sberbank Europe/Штефан Зочлинг): поле `date` несло только год «2022» —
без месяца и дня. Дельта нашла независимое подтверждение реальной даты
закрытия: Moscow Times (дата публикации 16 июня 2023, пятница) прямо
пишет «Sberbank has completed its exit from the European market with
the sale of its Austrian subsidiary, the bank said in a statement
Friday» — 16 июня 2023 действительно пятница. Три дополнительных
источника (Börse Express/«Standard», Falter, parlament.gv.at) независимо
называют ту же неделю июня 2023 года. Год «2022» в карточке, видимо,
взят из более раннего этапа истории продажи (санкции против Сбербанка
были введены в 2022), а не из даты самого закрытия сделки.

Не через review.py: перенос сделки в ДРУГОЙ год `review.py` не делает
никогда (сознательная граница `date_is_supported()` — см. CLAUDE.md,
«review.py не умеет переносить сделку в другой год — и не должен»).
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g5c3eeb06'
OLD_DATE = '2022'
NEW_DATE = '2023-06-16'


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['date'] == OLD_DATE, \
        f"date: неожиданное значение {deal['date']!r}"

    print(f"{CARD_ID} date: {OLD_DATE!r} -> {NEW_DATE!r} (Moscow Times, "
          "16 июня 2023, пятница — подтверждено тремя источниками)")
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
