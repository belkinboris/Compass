# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF) — новые источники, найденные
дельта-поиском 24 августа 2026 для g5dc6cb47 (ОСК/КМЗ); факты — в
eco.context/eco.val той же карточки (fix_kmz_osk_reversal_context.py,
fix_kmz_osk_kumanovsky_valuation.py).

Запуск: python3 pipeline/ingest/review.py --write
"""

FIXES = [
    dict(id='g5dc6cb47', field='src', old=None,
         new=['Фонтанка.ру (14.01.2026)', 'https://www.fontanka.ru/2026/01/14/76215445/'],
         quote='Доля этой компании, 99,9%, была возвращена от ОСК '
               'предыдущему владельцу — Татьяне Даниленко',
         why='возврат доли ОСК Даниленко и независимая оценка сделки'),
    dict(id='g5dc6cb47', field='src', old=None,
         new=['Фонтанка.ру (09.11.2025)', 'https://www.fontanka.ru/2025/11/09/76111870/'],
         quote='нестабильная экономическая ситуация',
         why='кризис с зарплатой на заводе в период владения ОСК'),
]
