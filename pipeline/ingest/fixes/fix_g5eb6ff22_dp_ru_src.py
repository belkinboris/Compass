# -*- coding: utf-8 -*-
"""Карточка `g5eb6ff22` — четвёртое подтверждение закрытия (dp.ru),
повторяет уже известные цитаты Шишкарева, нового факта нет — только src.

Источник: https://www.dp.ru/a/2026/10/07/rosatom-zakril-precedentnuju

Запуск: python3 pipeline/ingest/review.py [--write]
"""

FIXES = [
    dict(id='g5eb6ff22', field='src', old=None,
         new=['dp.ru', 'https://www.dp.ru/a/2026/10/07/rosatom-zakril-precedentnuju'],
         quote='Непреодолимые разногласия о будущем группы привели нас в точку, где наши пути сегодня расходятся',
         why='четвёртое подтверждение закрытия'),
]
