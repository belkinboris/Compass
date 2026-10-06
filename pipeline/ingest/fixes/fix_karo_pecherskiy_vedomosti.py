# -*- coding: utf-8 -*-
"""Карточка `g0710e7a1` (Печерский/«Каро») — первоисточник факта («Ведомости»,
5 октября 2026) найден саб-агентом; Mergers.ru пересказывал именно эту статью.
Обе стороны отказались от комментариев — честно отмечено в карточке, а не
придумана причина.

Источник: https://www.vedomosti.ru/media/articles/2026/10/05/1234489-grigorii-pecherskii-voshel-v-karo

Запуск: python3 pipeline/ingest/review.py [--write]
"""

VEDOMOSTI_URL = (
    'https://www.vedomosti.ru/media/articles/2026/10/05/'
    '1234489-grigorii-pecherskii-voshel-v-karo'
)

QUOTE = 'В пресс-службе «Каро» и ADG Group от комментариев отказались'

FIXES = [
    dict(id='g0710e7a1', field='src', old=None,
         new=['Ведомости', VEDOMOSTI_URL],
         quote=QUOTE,
         why='первоисточник, который пересказывал Mergers.ru'),
]
