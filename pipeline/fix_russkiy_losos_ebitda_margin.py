# -*- coding: utf-8 -*-
"""Месячная очередь, карточка g506ea8c4 (Курявый/«Русский лосось»):
дельта-поиск нашёл независимую оценку маржинальности бизнеса
(mergers.ru) — отдельный источник от того, из которого собрано текущее
значение `eco.val` (Коммерсантъ), поэтому не через `review.py`
(дословная проверка требует непрерывный кусок ОДНОГО источника).

Источник — читал напрямую (fetch_article_texts.py, закэширован):
https://mergers.ru/news/U-kompanii-Russkij-loslos-pomenyalsya-osnovnoj-akcioner-85419

Запуск: python3 pipeline/fix_russkiy_losos_ebitda_margin.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g506ea8c4'

OLD_VAL = 'Оценка EV 10–12 млрд руб; не раскрыта (оценка EV 10–12 млрд ₽)'
NEW_VAL = OLD_VAL + (
    ' По подсчетам инвестбанкира Ильи Шумова, маржинальность бизнеса '
    'по EBITDA может достигать 40%.'
)


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['val'] == OLD_VAL, f"eco.val: {deal['eco']['val']!r}"

    print(f'{CARD_ID} eco.val: += оценка маржинальности EBITDA (Шумов, mergers.ru)')

    if write:
        deal['eco']['val'] = NEW_VAL
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('ЗАПИСАНО')
    else:
        print('Сухой прогон. Запись — с --write.')


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
