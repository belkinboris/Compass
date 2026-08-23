# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), дельта-поиск 23 августа: источники
к g78986e22 (Альфа-банк/«Европлан», см.
fix_alfabank_europlan_integration_h1_2026.py) и g0a2088ba (MGC Group/
Grupo Antolin, см. fix_mgc_antolin_group_expansion_context.py). Сами
факты дописаны одноразовыми скриптами — здесь только ссылки.

Запуск: python3 pipeline/ingest/review.py --write
"""

FIXES = [
    dict(id='g78986e22', field='src', old=None,
         new=['Smart-Lab (интеграция)', 'https://smart-lab.ru/blog/1293354.php'],
         quote='Региональные офисы «Альфамобиля» станут обособленными подразделениями в сети «Европлана»',
         why='детали структуры интеграции «Альфамобиля» и «Европлана»'),
    dict(id='g78986e22', field='src', old=None,
         new=['Smart-Lab (МСФО I полугодие 2026)', 'https://smart-lab.ru/blog/1342001.php'],
         quote='Чистая прибыль составила 4,3 млрд руб. (+129% по сравнению с первым полугодием 2025)',
         why='финансовые результаты «Европлана» за I полугодие 2026 года'),
    dict(id='g0a2088ba', field='src', old=None,
         new=['Интерфакс (30.05.2026)', 'https://www.interfax.ru/business/1092800'],
         quote='MGC Group приобрел контроль в управляющей структуре калужского завода, собирающего Haval M6',
         why='продолжение экспансии MGC Group в автокомпонентном/автосборочном сегменте'),
]
