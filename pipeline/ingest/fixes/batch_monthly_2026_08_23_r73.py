# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка gadb5b474 (Ростех/
«Техсервис»): карточка держалась на одном источнике (Коммерсантъ) —
дельта-поиск нашёл независимый второй источник.

Запуск: python3 pipeline/ingest/review.py --write
"""

FIXES = [
    dict(
        id='gadb5b474', field='src', old=None,
        new=['zolteh.ru', 'https://zolteh.ru/news/dochernee_predpriyatie_rostekha_vyshlo_iz_zolotodobychi_v_irkutskoy_oblasti/'],
        quote='Дочерняя компания корпорации "Ростех" продала '
              'золотодобывающий актив в Иркутской области — ООО '
              '"Техсервис"',
        why='второй независимый источник',
    ),
]
