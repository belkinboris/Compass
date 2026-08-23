# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), дельта-поиск 23 августа: источники
к находкам по карточке g6fe7016f («Ростелеком»/ОМП/«Аврора»), дописанным
разовым скриптом fix_rostelecom_avrora_closing_and_tv.py.

Запуск: python3 pipeline/ingest/review.py --write
"""

FIXES = [
    dict(id='g6fe7016f', field='src', old=None,
         new=['Хабр', 'https://habr.com/ru/news/765514/'],
         quote='С 3 октября «Ростелеком» официально является '
               'владельцем 99,9%',
         why='источник точной даты и итоговой доли закрытия сделки'),
    dict(id='g6fe7016f', field='src', old=None,
         new=['Коммерсантъ', 'https://www.kommersant.ru/doc/8671023'],
         quote='Первая партия может составить 150–200 тыс. устройств '
               'до конца 2026 года',
         why='источник запуска «Аврора ТВ» (2025)'),
]
