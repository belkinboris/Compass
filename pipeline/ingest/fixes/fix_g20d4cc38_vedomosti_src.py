# -*- coding: utf-8 -*-
"""Карточка `g20d4cc38` (ЛУКОЙЛ/Carlyle) — второй источник на факт об
истечении январского соглашения.

Запуск: python3 pipeline/ingest/review.py [--write]
"""

FIXES = [
    dict(id='g20d4cc38', field='src',
         old=None,
         new=['Ведомости',
              'https://www.vedomosti.ru/business/news/2026/10/08/1235427-soglashenie-prodazhe'],
         quote='Соглашение «Лукойла» о продаже активов международного Lukoil '
               'International GmbH (LIG) американскому инвестиционному фонду '
               'Carlyle утратило силу.',
         why='источник на факт об истечении январского соглашения с Carlyle'),
]
