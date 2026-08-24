# -*- coding: utf-8 -*-
"""Карточка g4fc7af86 (Ipsos SA продала 80% доли в российском бизнесе и
создала СП) несла дату 2025-07-31 — это дата публикации Sostav.ru о
согласовании ходатайства ФАС, а не дата закрытия сделки. Официальный
пресс-релиз самой Ipsos SA (Совет директоров, распространён через
GlobeNewswire) прямо датирован и объявляет о ЗАКРЫТИИ:

«Paris, February 27, 2026 – Ipsos SA' Board of Directors announces the
Closing of the sale of 80% of Ipsos Comcon LLC»

Это перенос в другой ГОД (2025 → 2026), а не уточнение дня/месяца внутри
известного года — `review.py`'s `date_is_supported()` сознательно
отказывает в таких переносах (см. CLAUDE.md, «review.py не умеет
переносить сделку в другой год»), поэтому правка идёт отдельным
скриптом со своим `assert`, по тому же принципу, что и
`fix_osnova_sviblovo_date.py`.

Источник — читал напрямую (fetch_article_texts.py, закэширован):
https://www.investegate.co.uk/announcement/gnw/ipsos-sa--0ka3/-press-release-sale-of-80-of-ipsos-comcon-l-/9451927

Запуск: python3 pipeline/fix_ipsos_comcon_closing_date.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g4fc7af86'
OLD_DATE = '2025-07-31'
NEW_DATE = '2026-02-27'


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['date'] == OLD_DATE, f"date: неожиданное значение {deal['date']!r}"

    print(f"{CARD_ID} date: {OLD_DATE} -> {NEW_DATE} "
          f"(дата закрытия по официальному пресс-релизу Ipsos SA, а не "
          f"дата новости об одобрении ФАС)")
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
