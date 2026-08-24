# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g8a86fc9b (VK Tech/
CedrusData): CNews (независимый источник вместо телеграм-агрегатора
@dealsma) дал цель сделки — поле было пустым.

Запуск: python3 pipeline/ingest/review.py --write
"""

FIXES = [
    dict(
        id='g8a86fc9b', field='eco.rationale', old=None,
        new='Сделка направлена на развитие и усиление продуктовой '
            'линейки VK Tech в области хранения, обработки, анализа '
            'данных и ИИ.',
        quote='Сделка направлена на развитие и усиление продуктовой '
              'линейки VK Tech в области хранения, обработки, анализа '
              'данных и ИИ.',
        why='CNews: цель сделки — поле было пустым',
    ),
    dict(id='g8a86fc9b', field='src', old=None,
         new=['CNews', 'https://www.cnews.ru/news/line/2026-03-26_vk_tech_usilivaet_napravlenie'],
         quote='Сделка направлена на развитие и усиление продуктовой '
               'линейки VK Tech в области хранения, обработки, анализа '
               'данных и ИИ.',
         why='независимый источник вместо телеграм-агрегатора @dealsma'),
]
