# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка ga7e96633 (B2B-РТС):
`status` стоял «Обсуждается», `date` — 2025-11-01 (дата ОБЪЯВЛЕНИЯ
намерения провести IPO). Дельта нашла: IPO фактически СОСТОЯЛОСЬ 17
апреля 2026 года — Ведомости (уже в `src` карточки, читались при
недельной дельте) прямо пишут «B2B-РТС провела на Московской бирже
первичное публичное размещение (IPO) акций на 2,43 млрд руб.»
(17 апреля 2026, 10:46). Статус карточки был устаревшим на 4 месяца —
именно тот класс дефекта, который REVISION_BRIEF называет обязательной
проверкой для незакрытых сделок.

Не через review.py:
- Перенос ГОДА (2025 -> 2026) `review.py` не делает никогда
  (`date_is_supported()`, см. CLAUDE.md).
- Слово «провела» не входит в список STATUS_WORDS для статуса «Закрыта»
  (там «закрыл», «завершила» и т.п., но не «провела») — механическая
  проверка отказала бы в правке, хотя факт закрытия сделки дословно
  подтверждён тем же предложением.
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'ga7e96633'
OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Закрыта'
OLD_DATE = '2025-11-01'
NEW_DATE = '2026-04-17'


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['status'] == OLD_STATUS, \
        f"status: неожиданное значение {deal['status']!r}"
    assert deal['date'] == OLD_DATE, \
        f"date: неожиданное значение {deal['date']!r}"

    print(f"{CARD_ID} status: {OLD_STATUS!r} -> {NEW_STATUS!r} (IPO "
          "состоялось 17 апреля 2026, Ведомости)")
    print(f"{CARD_ID} date: {OLD_DATE!r} -> {NEW_DATE!r} (дата "
          "закрытия IPO, а не дата объявления намерения)")
    deal['status'] = NEW_STATUS
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
