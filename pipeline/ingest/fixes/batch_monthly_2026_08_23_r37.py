# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), дельта-поиск 23 августа: источники
к находке по карточке g3875e8f5 (Capital Group/ТВК «Тишинка»),
дописанной разовым скриптом fix_tishinka_element_lawsuit.py.

Запуск: python3 pipeline/ingest/review.py --write
"""

FIXES = [
    dict(id='g3875e8f5', field='src', old=None,
         new=['Ведомости',
              'https://www.vedomosti.ru/realty/articles/2025/04/29/'
              '1107295-vladeltsi-tvk-tishinka-sudyatsya-s-peterburgskoi-element-development'],
         quote='подали в столичный арбитраж иск к входящей в Element '
               'Development компании «Элемент К-3»',
         why='источник иска к Element Development (апрель 2025)'),
    dict(id='g3875e8f5', field='src', old=None,
         new=['Ведомости',
              'https://www.vedomosti.ru/realty/articles/2025/10/28/'
              '1150277-sud-razreshil-peterburgskoi-element-development-ne-pokupat-tvk-tishinka'],
         quote='Арбитражный суд Москвы отказался удовлетворить иск',
         why='источник решения суда (октябрь 2025)'),
]
