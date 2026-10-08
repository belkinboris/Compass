# -*- coding: utf-8 -*-
"""Карточка `g20d4cc38` (ЛУКОЙЛ/Carlyle) — источник на отказ OFAC и поиск
нового покупателя.

Запуск: python3 pipeline/ingest/review.py [--write]
"""

FIXES = [
    dict(id='g20d4cc38', field='src',
         old=None,
         new=['Право.ru', 'https://pravo.ru/news/266214/'],
         quote='Теперь компания ищет нового покупателя на группу компаний LIG.',
         why='отказ OFAC и поиск нового покупателя на LIG'),
]
