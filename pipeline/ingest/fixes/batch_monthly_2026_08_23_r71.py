# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g1b5e8ab8 (Raiffeisen):
источники для смены CEO и иска к Rasperia, добавленных
fix_raiffeisen_ceo_and_rasperia_lawsuit.py.

Запуск: python3 pipeline/ingest/review.py --write
"""

FIXES = [
    dict(
        id='g1b5e8ab8', field='src', old=None,
        new=['EQS-News (17.12.2025)',
             'https://www.eqs-news.com/news/ad-hoc/raiffeisen-bank-international-ag-michael-hollerer-will-succeed-johann-strobl-as-ceo-of-rbi-on-1-july-2026/7159e11d-5ea2-48ad-a80e-50265dbee62b_en'],
        quote='The Supervisory Board of Raiffeisen Bank International AG '
              '(RBI) has today appointed Michael Höllerer as Johann '
              'Strobl’s successor as CEO of RBI',
        why='объявление о смене CEO',
    ),
    dict(
        id='g1b5e8ab8', field='src', old=None,
        new=['Vindobona (09.08.2026)',
             'https://www.vindobona.org/article/landmark-3-15-billion-lawsuit-austrian-rbi-sues-russian-rasperia-in-a-vienna-court'],
        quote='Raiffeisen Bank International (RBI) is the first '
              'European company to invoke Article 11a of the 14th EU '
              'sanctions package',
        why='иск RBI к Rasperia на 3,15 млрд евро',
    ),
]
