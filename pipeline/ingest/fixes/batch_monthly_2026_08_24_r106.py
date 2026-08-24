# -*- coding: utf-8 -*-
"""Месячная очередь: источники для fix_lesart_gevorkyan_exit_context.py.

Запуск: python3 pipeline/ingest/review.py --write
"""

FIXES = [
    dict(id='g016f1b13', field='src', old=None,
         new=['msk1.ru', 'https://msk1.ru/text/incidents/2024/11/13/74329517/'],
         quote='Сейчас гостиничным комплексом управляет компания ООО '
               '«Лесресорт», она принадлежит Рузанне Абрамян',
         why='структура владения активом до сделки'),
    dict(id='g016f1b13', field='src', old=None,
         new=['Коммерсантъ', 'https://www.kommersant.ru/doc/7497718'],
         quote='В 2022-м Вазген Симонович Геворкян перестал участвовать '
               'в управлении данным активом, а в 2023-м продал свою '
               'долю в нем',
         why='подтверждение выхода Геворкяна из актива в 2023 году'),
]
