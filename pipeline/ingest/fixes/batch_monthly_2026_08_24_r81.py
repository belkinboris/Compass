# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF) — новые источники, найденные
дельта-поиском 24 августа 2026 для g630c3361 (ГК «Медскан»/«Нетрика
Медицина»); факты — в eco.context и eco.target_fin той же карточки
(fix_medskan_netrika_negotiations_context.py,
fix_medskan_netrika_2025_financials.py).

Запуск: python3 pipeline/ingest/review.py --write
"""

FIXES = [
    dict(id='g630c3361', field='src', old=None,
         new=['Ведомости', 'https://www.vedomosti.ru/health/medicine_future/characters/2026/01/30/1173011-meditsinskogo-rinka'],
         quote='Сейчас мы ведем переговоры о вхождении компании в наш '
               'контур, что позволит более эффективно реализовать планы '
               'по запуску проекта.',
         why='подтверждение статуса «Обсуждается» на 30.01.2026 — '
             'переговоры продолжаются'),
    dict(id='g630c3361', field='src', old=None,
         new=['Коммерсантъ', 'https://www.kommersant.ru/doc/8549598'],
         quote='Мы целимся в осеннее окно. Сейчас мы в принципе на 80% '
               'готовы организационно.',
         why='мотив сделки со стороны «Медскана» — подготовка к IPO'),
    dict(id='g630c3361', field='src', old=None,
         new=['vaskov.pro (ГИР БО)', 'https://vaskov.pro/company/1001185123'],
         quote='ООО "НЕТРИКА МЕДИЦИНА", ИНН 1001185123 — сведения из '
               'бухгалтерской отчётности ГИР БО за 2025: выручка 926,4 '
               'млн ₽, чистая прибыль 316,6 млн ₽.',
         why='финансы предмета сделки за 2025 год'),
]
