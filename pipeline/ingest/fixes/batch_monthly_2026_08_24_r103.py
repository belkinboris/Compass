# -*- coding: utf-8 -*-
"""Месячная очередь: источник для fix_renessans_eag_option_not_exercised.py.

Запуск: python3 pipeline/ingest/review.py --write
"""

FIXES = [
    dict(id='ge2e2c71c', field='src', old=None,
         new=['Shoppers.Media', 'https://shoppers.media/news/27711_proizvoditel-santo-stefano-mozet-vypustit-limonady'],
         quote='На конец года 50% осталось у «РТД боттлерс»',
         why='структура владения на конец 2025 года, опцион не '
             'реализован'),
]
