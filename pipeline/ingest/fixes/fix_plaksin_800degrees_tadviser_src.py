# -*- coding: utf-8 -*-
"""Карточка `g33051f70` (Плаксин/«800 Degrees») — второй источник
(TAdviser, пересказ того же факта из СПАРК через Коммерсантъ).

Источник: https://www.tadviser.ru/a/970944

Запуск: python3 pipeline/ingest/review.py [--write]
"""

QUOTE = (
    'Владелец платформы по развитию брендов Giper.fm Максим Плаксин '
    'приобрел 25% компании 800 Degrees, выпускающей товары для барбекю и '
    'отдыха.'
)

FIXES = [
    dict(id='g33051f70', field='src', old=None,
         new=['TAdviser', 'https://www.tadviser.ru/a/970944'],
         quote=QUOTE,
         why='второй источник того же факта'),
]
