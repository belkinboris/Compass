# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g4ba9150f (Светогорский
ЦБК/«ЭвоКом»): источники для подтверждения закрытия сделки и
ребрендинга, добавленных fix_svetogorsky_evokom_status_closed.py.

Запуск: python3 pipeline/ingest/review.py --write
"""

FIXES = [
    dict(
        id='g4ba9150f', field='src', old=None,
        new=['Коммерсантъ (16.11.2025)', 'https://www.kommersant.ru/doc/8210001'],
        quote='Ранее пакет в "ЭвоКом" получили структуры Светогорского '
              'ЦБК',
        why='подтверждение закрытия сделки задним числом',
    ),
    dict(
        id='g4ba9150f', field='src', old=None,
        new=['Retail.ru (30.03.2026)',
             'https://www.retail.ru/news/evokom-ofitsialno-pereimenoval-zewa-v-zemma-30-marta-2026-276087/'],
        quote='«Для нас принципиально важно было не просто сменить '
              'название, а сохранить то, за что потребители ценят '
              'Zewa», — отметил генеральный директор ООО "ЭвоКом" Артем '
              'Лебедев',
        why='ребрендинг Zewa в Zemma, актив жив и работает в 2026 году',
    ),
]
