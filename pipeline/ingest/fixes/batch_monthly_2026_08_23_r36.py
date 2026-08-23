# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), дельта-поиск 23 августа: источник
к находке по карточке g7c8f9112 (Softline Venture Partners/HR Rocket),
дописанной разовым скриптом fix_hrrocket_full_cap_table.py.

Запуск: python3 pipeline/ingest/review.py --write
"""

FIXES = [
    dict(id='g7c8f9112', field='src', old=None,
         new=['vc.ru', 'https://vc.ru/id4994551/'
              '2689266-investicii-softline-v-ii-platformu-hr-rocket'],
         quote='Согласно данным Rusprofile, гендиректору ООО "Эйчар '
               'Рокет" Дмитрию Саушкину принадлежит 22,82%',
         why='источник полной структуры капитала после сделки (доли '
             'основателей)'),
]
