# -*- coding: utf-8 -*-
"""Месячная очередь, карточка g34cab70b («Русагро»/ООО «Центральное»):
дата стояла «2025» (год без месяца/дня, единственный источник —
телеграм-агрегатор @dealsma), но независимый источник (Коммерсантъ)
публикует новость о закрытии сделки 19 февраля 2026 года — точный день
подписания документов источник не называет, поэтому в `date` идёт
только год, без выдуманного дня (тот же приём, что уже применялся к
датам-заглушкам). `review.py`'s `date_is_supported()` не умеет
переносить сделку в другой год — год меняется отдельным скриптом.

Источник — читал напрямую (WebFetch, дословные цитаты подтверждены):
https://www.kommersant.ru/doc/8443121

Запуск: python3 pipeline/fix_rusagro_centralnoe_year.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g34cab70b'
OLD_DATE = '2025'
NEW_DATE = '2026'


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['date'] == OLD_DATE, f"date: неожиданное значение {deal['date']!r}"

    print(f'{CARD_ID} date: {OLD_DATE!r} -> {NEW_DATE!r} '
          f'(Коммерсантъ публикует новость о закрытии 19 февраля 2026 '
          f'года, точный день подписания не назван — только год)')

    if write:
        deal['date'] = NEW_DATE
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('ЗАПИСАНО')
    else:
        print('Сухой прогон. Запись — с --write.')


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
