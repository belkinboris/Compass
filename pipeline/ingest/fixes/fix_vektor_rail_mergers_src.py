# -*- coding: utf-8 -*-
"""Карточка `gdffd613c` («Вектор Рейл») — Mergers.ru подтвердил третий
провал аукциона (5 октября 2026) тем же фактом, что уже есть в карточке
(РБК, 2 октября): ещё одна цитируемость, без новых фактов в полях.

Источник: https://mergers.ru/news/PSB-v-tretij-raz-ne-smog-prodat-nacionalizirovannyj-Vektor-Rejl-87607

Запуск: python3 pipeline/ingest/review.py [--write]
"""

MERGERS_URL = (
    'https://mergers.ru/news/PSB-v-tretij-raz-ne-smog-prodat-'
    'nacionalizirovannyj-Vektor-Rejl-87607'
)

QUOTE = (
    'Аукцион по продаже национализированной в августе 2025 года лизинговой '
    'компании «Вектор Рейл» вновь признан несостоявшимся.'
)

FIXES = [
    dict(id='gdffd613c', field='src', old=None,
         new=['Mergers.ru', MERGERS_URL],
         quote=QUOTE,
         why='ещё один источник третьего провала аукциона, факт уже в карточке'),
]
