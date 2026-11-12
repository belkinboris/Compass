# -*- coding: utf-8 -*-
"""Вычитка 12 ноября 2026, партия m032 (марафон), вторая часть: источники, добавленные к карточкам.

Проза — write_card.py (план партии), стороны, даты, заголовки и профили — разовый скрипт
pipeline/archive/2026-11/reread_oneoff_m032b.py (там же след поиска по каждой карточке).
Тексты источников сохранены save_source.py в data/inbox/triage/sources_2026-11-12_m032.json.

Запуск: python3 pipeline/ingest/review.py [--write]
"""

CARDS = ['gaa0ca672', 'g5a1ee21e', 'g39218eec', 'g073bf58b']

_W = 'вычитка 12 ноября 2026 (партия m032) по статьям, сохраненным save_source.py; '

FIXES = [
    {'id': 'gaa0ca672', 'field': 'src', 'old': None,
     'new': ['ComNews', 'https://www.comnews.ru/content/233967/2024-06-26/2024-w26/1010/'
                        'struktura-gk-softline-priobretaet-kontroliruyuschuyu-dolyu-md-audit'],
     'quote': 'Андрей Подгорнов, генеральный директор ООО "МД Аудит", присоединяется к SL Soft в роли руководителя '
              'кластера розничных решений',
     'why': _W + 'пресс-релиз Softline о сделке: условия для гендиректора (law.terms) и цель'},
    {'id': 'g5a1ee21e', 'field': 'src', 'old': None,
     'new': ['Gmk.center', 'https://gmk.center/news/cleveland-cliffs-vedet-peregovory-o-pokupke-amerikanskih-zavodov-nlmk-bloomberg/'],
     'quote': 'Активы НЛМК – металлургические мощности в Индиане и Пенсильвании – при возможной продаже могут быть '
              'оценены более чем в $500 млн.',
     'why': _W + 'пересказ Bloomberg (сама статья за пейволом): предмет, оценка, история заводов'},
    {'id': 'g39218eec', 'field': 'src', 'old': None,
     'new': ['CNews', 'https://www.cnews.ru/news/top/2025-03-13_softline_potratit_bolshe_300_mln'],
     'quote': 'То есть полная сумма сделки составила 162 млн руб.',
     'why': _W + 'раскрытие Softline: цена и состав расчета'},
    {'id': 'g073bf58b', 'field': 'src', 'old': None,
     'new': ['Interfax.com', 'https://interfax.com/newsroom/top-stories/103868/'],
     'quote': 'has become the sole owner of BASF Wostok, the Russian coatings division of German chemicals giant BASF',
     'why': _W + 'закрытие по ЕГРЮЛ'},
]
