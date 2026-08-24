# -*- coding: utf-8 -*-
"""Месячная очередь, карточка g081ac83c (ГК «Солар»/«СОФТ ПЛЮС», Hexway):
у оценки сделки нашлось два расходящихся мнения аналитиков (ComNews) —
Леонид Делицын (500 млн ₽) уже внесён через review.py, Владимир Чернов
не согласен и называет диапазон 2-3 млрд ₽. Не через review.py: между
двумя цитатами в источнике лежит посторонний текст (ссылка на другую
статью, вклинившаяся при разборе страницы) — не образует непрерывный
кусок с уже принятой цитатой Делицына.

Источник — читал напрямую (fetch_article_texts.py, закэширован):
https://www.comnews.ru/content/240773/2025-08-19/2025-w34/1007/solar-poglotil-90-ooo-soft-plyus-dva-zakhoda

Запуск: python3 pipeline/fix_solar_hexway_chernov_valuation.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g081ac83c'

OLD_VAL = (
    '«90% компании я оцениваю в 500 млн руб. Выручка «Солар» сейчас '
    'приблизительно в 200 раз больше, чем выручка приобретаемого '
    'актива, так что на финансовых показателях «Солар» сделка отразится '
    'слабо. Гораздо важнее возможность получить заметную долю '
    'перспективной ниши рынка и предоставлять клиентам широкий диапазон '
    'востребованных услуг», — сказал Леонид Делицын.'
)
ADDITION = (
    'С его оценкой не согласился Владимир Чернов: по его словам, если '
    'ориентироваться на сопоставимые сделки и динамику рынка, то '
    'стоимость Hexway составляет от 2 млрд до 3 млрд руб.'
)
NEW_VAL = OLD_VAL + ' ' + ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['val'] == OLD_VAL, \
        f"eco.val: неожиданное значение {deal['eco']['val']!r}"

    print(f"{CARD_ID} eco.val: += вторая, расходящаяся оценка "
          f"(Владимир Чернов, 2-3 млрд ₽)")
    deal['eco']['val'] = NEW_VAL

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО")
    else:
        print("Сухой прогон. Запись — с --write.")


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
