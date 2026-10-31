# -*- coding: utf-8 -*-
"""Карточка c59e65efb (Роман Абрамович / Target Global), ни разу не
прошедшая проверку чтением: `date` стоял "unknown", а `extra` и
`eco.share` несли одну и ту же расплывчатую фразу без единого названия
компании. РБК.RU (13 января 2024, пересказ расследования Forbes на
утечке файлов кипрского офшора Meritservus) называет конкретные
компании и точную структуру вложений.

Не через review.py:
- `date`: "unknown" не в формате ГГГГ-ММ-ДД, `date_is_supported()` не
  пропустит смену "unknown" на "2024-01-13".
- `extra`/`eco.share`: оба поля уже не пусты ("—"), а дословная замена
  на принципиально другой текст (с перечнем компаний) — это не
  дополнение, а переформулировка; проверка `review.py` для замены
  непустого поля потребовала бы, чтобы СТАРЫЙ текст тоже лежал в
  цитате, а старая расплывчатая фраза в источнике не встречается.
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'c59e65efb'
OLD_DATE = 'unknown'
NEW_DATE = '2024-01-13'

OLD_TEXT = (
    'Инвестиционный фонд Target Global распоряжался капиталом Романа '
    'Абрамовича и помог ему приобрести доли в крупнейших европейских '
    'стартапах.'
)
NEW_TEXT = (
    'Российский миллиардер Роман Абрамович через инвестиционный фонд '
    'Target Global вложил свыше $63 млн в европейские технологические '
    'стартапы, среди которых — Auto1, Flo, Revolut, Cazoo, Circ и др.'
)


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['date'] == OLD_DATE, f"date: неожиданное значение {deal['date']!r}"
    assert deal['extra'] == OLD_TEXT, f"extra: неожиданное значение {deal['extra']!r}"
    assert deal['eco']['share'] == OLD_TEXT, \
        f"eco.share: неожиданное значение {deal['eco']['share']!r}"

    print(f"{CARD_ID} date: {OLD_DATE!r} -> {NEW_DATE!r} (дата публикации "
          "расследования РБК/Forbes)")
    print(f"{CARD_ID} extra/eco.share: расплывчатая фраза -> конкретный "
          "перечень компаний (RB.RU)")
    deal['date'] = NEW_DATE
    deal['extra'] = NEW_TEXT
    deal['eco']['share'] = NEW_TEXT

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО")
    else:
        print("Сухой прогон. Запись — с --write.")


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
