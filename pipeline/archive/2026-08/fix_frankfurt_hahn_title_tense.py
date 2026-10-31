# -*- coding: utf-8 -*-
"""Продолжение fix_frankfurt_hahn_deal_failed.py (та же карточка,
g21c5ee1e): после смены статуса на «Не состоялась» заголовок
«NR Holding покупает немецкий аэропорт Франкфурт-Хан» остался в
настоящем времени — прямое противоречие статусу (см. CLAUDE.md, «Разное
время в заголовках — не всегда разнобой»: здесь разнобой РЕАЛЬНЫЙ, само
действие не совершилось). Найдено визуальной проверкой экрана после
записи предыдущего скрипта, а не при его написании.
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g21c5ee1e'
OLD_TITLE = 'NR Holding покупает немецкий аэропорт Франкфурт-Хан'
NEW_TITLE = 'Сделка NR Holding по покупке аэропорта Франкфурт-Хан сорвалась'


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['title'] == OLD_TITLE, f"title: неожиданное значение {deal['title']!r}"
    assert deal['status'] == 'Не состоялась', \
        f"status: ожидали «Не состоялась», в базе {deal['status']!r}"

    print(f"{CARD_ID} title: {OLD_TITLE!r} -> {NEW_TITLE!r}")
    deal['title'] = NEW_TITLE

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО")
    else:
        print("Сухой прогон. Запись — с --write.")


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
