# -*- coding: utf-8 -*-
"""Вычитка 12 ноября 2026, партия m032 (марафон): источники, добавленные к карточкам.

Проза — write_card.py (план партии), стороны, суммы, заголовки и профили — разовый скрипт
pipeline/archive/2026-11/reread_oneoff_m032.py (там же след поиска по каждой карточке).
Тексты источников сохранены save_source.py в data/inbox/triage/sources_2026-11-12_m032.json.

Запуск: python3 pipeline/ingest/review.py [--write]
"""

CARDS = ['g9d09dc7c', 'g88236336']

_W = 'вычитка 12 ноября 2026 (партия m032) по статьям, сохраненным save_source.py; '

FIXES = [
    {'id': 'g9d09dc7c', 'field': 'src', 'old': None,
     'new': ['АК&М', 'https://www.akm.ru/news/tmk_prodala_tmk_yamz/'],
     'quote': 'ТМК закрыла сделку по продаже Ярцевского метзавода (ТМК-ЯМЗ) стороннему инвестору.',
     'why': _W + 'сообщение о закрытии с условиями для нового собственника (law.terms)'},
    {'id': 'g88236336', 'field': 'src', 'old': None,
     'new': ['ComNews', 'https://www.comnews.ru/content/233738/2024-06-14/2024-w24/1009/'
                        'byvshiy-zamglavy-minpromtorga-stal-sovladelcem-proizvoditelya-bankomatov'],
     'quote': 'Он объяснил свое решение купить долю в BFS тем, что компания полностью соответствует перечисленным критериям',
     'why': _W + 'мотив покупателя (eco.rationale)'},
]
