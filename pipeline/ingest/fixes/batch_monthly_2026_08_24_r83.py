# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF) — новые источники, найденные
дельта-поиском 24 августа 2026 для g1d1ac507 (Сбер/«Еаптека»/Репик) и
g2197ed53 (Газпромбанк/«Медскан»); факты — в eco.context тех же карточек
(fix_sber_eapteka_resale_to_rwb_context.py,
fix_gazprombank_medskan_denial_context.py).

Запуск: python3 pipeline/ingest/review.py --write
"""

FIXES = [
    dict(id='g1d1ac507', field='src', old=None,
         new=['Vademecum', 'https://www.vademec.ru/news/2026/07/01/rvb-poluchila-kontrol-nad-eaptekoy/'],
         quote='В июле 2025 года 90% компании были консолидированы МКООО '
               '«Амсел», принадлежащей Репику, 10% в уставном капитале '
               '«Еаптеки» тогда перешли самому бизнесмену.',
         why='механика перехода последних 10% Буздалина + дальнейшая '
             'перепродажа RWB/Wildberries'),
    dict(id='g1d1ac507', field='src', old=None,
         new=['CNews', 'https://www.cnews.ru/news/top/2026-07-01_wildberries_prevrashchaetsya_v_apteku'],
         quote='По оценке директора по развитию аналитической компании '
               'RNC Pharma Николая Беспалова, бизнес «Еаптеки» стоил '
               'примерно 7-12 млрд руб. без учета долгов.',
         why='независимая оценка стоимости на момент перепродажи RWB'),
    dict(id='g2197ed53', field='src', old=None,
         new=['Коммерсантъ', 'https://www.kommersant.ru/doc/8293582'],
         quote='На вопрос ведущего, не про Газпромбанк ли говорит '
               'основатель компании, Евгений Туголуков ответил: «Нет, не '
               'про это».',
         why='публичное опровержение основателя «Медскана»'),
    dict(id='g2197ed53', field='src', old=None,
         new=['Ведомости', 'https://www.vedomosti.ru/business/articles/2026/06/03/1202334-u-medskana-poyavilsya-novii-investor'],
         quote='Также медицинская группа провела допэмиссию '
               'привилегированных акций типа А, которые приобрел один из '
               'финансовых инвесторов, сообщил представитель «Медскана», '
               'не раскрывая конкретного покупателя.',
         why='допэмиссия без названного покупателя, анонимный источник '
             'называет Газпромбанк'),
]
