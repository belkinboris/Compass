# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), дельта-поиск 23 августа: карточка
g8a66f3c7 (Рег.ру/Reddock) — источники цитаты владельца Reddock и
повторной сделки с Eternalhost (дописаны в eco.context отдельным
скриптом, см. fix_regru_reddock_context.py).

Запуск: python3 pipeline/ingest/review.py --write
"""

FIXES = [
    dict(id='g8a66f3c7', field='src', old=None,
         new=['CNews', 'https://www.cnews.ru/news/line/2024-02-13_regru_obyavil_o_sdelke'],
         quote='мы пришли к решению прекратить развитие провайдерских '
               'услуг',
         why='источник цитаты владельца Reddock о причине продажи'),
    dict(id='g8a66f3c7', field='src', old=None,
         new=['ComNews',
              'https://www.comnews.ru/content/232481/2024-04-05/'
              '2024-w14/1010/regru-poglotil-eternalhost'],
         quote='Требования к хостинг-провайдерам со стороны государства '
               'постоянно растут',
         why='источник повторной сделки Рег.ру с Eternalhost (та же '
             'стратегия консолидации)'),
]
