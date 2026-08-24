# -*- coding: utf-8 -*-
"""Этап 9, П0-9: сколько сторон/предмета в базе — пословный (с падежным
допуском) повтор заголовка, а не новый факт.

ЗАЧЕМ ОТДЕЛЬНЫЙ ЗАМЕР, А НЕ ПРОСТО «ПОСМОТРЕТЬ НА ПОСТ». Первое
приближение (substring, 24 августа) нашло 91/207 предметов и 461/968
сторон — но substring недосчитывает: «неназванную» (заголовок) и
«неназванная» (карточка) не совпадают по символам, хотя это одно слово в
разных падежах. `format_post.has_novelty()` (тот же компаратор, что
`review._same_word`) считает честно — и число НЕ падает, а растёт: точная
проверка ловит падежные пары, которые substring пропускал.

Запуск:
    python3 pipeline/publish/measure_headline_echo.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

import format_post as fp  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def measure():
    base = json.load(open(DATA, encoding='utf-8'))
    deals, companies = base['deals'], base['companies']

    echo_asset = total_asset = 0
    echo_party = total_party = 0
    for d in deals:
        seller, asset, buyer = fp.party_names(d, companies)
        title = d.get('title') or ''
        if asset:
            total_asset += 1
            if not fp.has_novelty(asset, title):
                echo_asset += 1
        for name in (seller, buyer):
            if name:
                total_party += 1
                if not fp.has_novelty(name, title):
                    echo_party += 1

    print('Предмет — чистый повтор заголовка: %d/%d (%.0f%%)'
          % (echo_asset, total_asset, 100 * echo_asset / total_asset if total_asset else 0))
    print('Продавец/Покупатель текстом — чистый повтор заголовка: %d/%d (%.0f%%)'
          % (echo_party, total_party, 100 * echo_party / total_party if total_party else 0))


if __name__ == '__main__':
    measure()
