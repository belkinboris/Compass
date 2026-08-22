# -*- coding: utf-8 -*-
"""Карточка c788bf9cc (Яндекс / Yango Israel, переговоры с Бараком
Абрамовым), ни разу не прошедшая проверку чтением: `date` стоял
"unknown", `status` не был проставлен вовсе. RB.RU (10 августа 2023)
прямо пишет: «Договоренность о сделке так и не была достигнута» — эти
конкретные переговоры сорвались.

Не через review.py:
- `date`: "unknown" не в формате ГГГГ-ММ-ДД.
- `status`: цитата не содержит ни одного триггер-слова из
  STATUS_WORDS['Не состоялась'] ('не состоял', 'отказал', 'прекращен',
  'отменен', 'отменён', 'не будет', 'отозв') — формулировка «так и не
  была достигнута» смысл передаёт, а механическая проверка нет.

Отдельно (не в этом скрипте): позже, в марте 2024 года, франшиза Yango
в Израиле всё же перешла ДРУГОЙ группе инвесторов во главе с Ашером
Маозом (Calcalist/israelinfo.co.il) — это отдельная сделка с другим
покупателем и другой структурой (франшиза, не M&A), не переносится в
эту карточку структурными полями (buyer и т.п.), только упоминается в
`eco.context` как дальнейшая судьба истории, через review.py.
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'c788bf9cc'
OLD_DATE = 'unknown'
NEW_DATE = '2023-08-10'
NEW_STATUS = 'Не состоялась'


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['date'] == OLD_DATE, f"date: неожиданное значение {deal['date']!r}"
    assert deal.get('status') is None, f"status: неожиданное значение {deal.get('status')!r}"

    print(f"{CARD_ID} date: {OLD_DATE!r} -> {NEW_DATE!r} (дата публикации RB.RU)")
    print(f"{CARD_ID} status: None -> {NEW_STATUS!r} (переговоры с Бараком "
          "Абрамовым не привели к сделке)")
    deal['date'] = NEW_DATE
    deal['status'] = NEW_STATUS

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО")
    else:
        print("Сухой прогон. Запись — с --write.")


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
