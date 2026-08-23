# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), дельта-поиск 23 августа: источники
к gd5741cbd (1С/AIINS, см. fix_aiins_reso_partnership.py) и ge848daa0
(МТС Страхование, см. fix_mts_strahovanie_rename_and_license.py). Сами
факты дописаны одноразовыми скриптами — здесь только ссылки.

Запуск: python3 pipeline/ingest/review.py --write
"""

FIXES = [
    dict(id='gd5741cbd', field='src', old=None,
         new=['CNews Safe (15.07.2026)', 'https://safe.cnews.ru/news/line/2026-07-15_reso-garantiya_i_insurtech-platforma'],
         quote='РЕСО-Гарантия" и InsurTech-платформа AIINS (совместное предприятие с фирмой "1С") объявили о начале стратегического партнерства',
         why='стратегическое партнёрство AIINS с РЕСО-Гарантия'),
    dict(id='ge848daa0', field='src', old=None,
         new=['МТС Страхование (сайт компании)', 'https://insurance.mts.ru/'],
         quote='ООО РНКБ Страхование сменило наименование на ООО «МТС Страхование»',
         why='переименование компании и новые лицензии'),
]
