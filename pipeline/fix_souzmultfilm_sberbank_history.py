# -*- coding: utf-8 -*-
"""Месячная очередь, карточка gb8717464 (Сбербанк выкупил 100% акций
«Союзмультфильма» у государства): дельта-поиск нашёл важную
предысторию отношений сторон — в 2020 году Сбербанк уже входил в
капитал студии через совместное предприятие (80%), но летом 2022 года
вышел из него из-за санкций. Это объясняет, почему нынешняя сделка —
не первый заход банка на актив.

Не через `review.py`: новый источник (RTVI) не образует с уже
записанным текстом `eco.context` непрерывный кусок.

Источник — читал напрямую (WebFetch, дословные цитаты подтверждены):
https://rtvi.com/news/stalo-izvestno-kto-kupil-soyuzmultfilm-u-gosudarstva/

Запуск: python3 pipeline/fix_souzmultfilm_sberbank_history.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gb8717464'

OLD_CONTEXT = (
    'Сделка по приватизации «Союзмультфильма» принесла российскому '
    'бюджету дополнительные доходы в размере 1,118 млрд рублей.'
)
CONTEXT_ADDITION = (
    ' В 2020 году Сбербанк и «Союзмультфильм» создали совместное '
    'предприятие (СП) ООО «Союзмультфильм». Банк получил в нем 80%. '
    'После того, как Сбербанк попал под санкции, кредитная организация '
    'летом 2022 года вышла из совместного предприятия с киностудией.'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"

    print(f'{CARD_ID} eco.context: {OLD_CONTEXT!r} -> история СП со '
          f'Сбербанком 2020-2022')

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        deal.setdefault('src', [])
        entry = ['RTVI', 'https://rtvi.com/news/stalo-izvestno-kto-kupil-soyuzmultfilm-u-gosudarstva/']
        if entry not in deal['src']:
            deal['src'].append(entry)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('ЗАПИСАНО')
    else:
        print('Сухой прогон. Запись — с --write.')


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
