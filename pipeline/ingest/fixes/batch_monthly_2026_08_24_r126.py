# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка ge361bfa8 (структуры
Виктора Харитонина/российский бизнес Reckitt): retailer.ru (второй
независимый источник) дал цель интереса покупателя — поле было
пустым.

Запуск: python3 pipeline/ingest/review.py --write
"""

FIXES = [
    dict(
        id='ge361bfa8', field='eco.rationale', old=None,
        new='Интерес к активу обусловлен брендами, отмечают '
            'источники.',
        quote='Интерес к активу обусловлен брендами, отмечают '
              'источники.',
        why='retailer.ru: цель покупателя — поле было пустым',
    ),
    dict(id='ge361bfa8', field='src', old=None,
         new=['retailer.ru', 'https://retailer.ru/farmstandart-viktora-haritonina-zainteresovalsja-pokupkoj-rossijskogo-biznesa-reckitt-benckiser/'],
         quote='Интерес к активу обусловлен брендами, отмечают '
               'источники.',
         why='второй независимый источник исходного предложения'),
]
