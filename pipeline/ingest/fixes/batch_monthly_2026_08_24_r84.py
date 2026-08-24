# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка gb4fad654 (КСЭ/BXB —
международное направление Boxberry): дельта-поиск нашёл финансы
предмета за 2024 год (CNews) и плановую цель партнёрства по доле рынка
(ecomhub.ru) — оба поля были пустыми.

Запуск: python3 pipeline/ingest/review.py --write
"""

FIXES = [
    dict(
        id='gb4fad654', field='eco.target_fin', old='—',
        new='Выручка «Биэксби рус» в 2024 г. составила 332 млн руб., '
            'чистая прибыль – 30 млн руб.',
        quote='Выручка «Биэксби рус» в 2024 г. составила 332 млн руб., '
              'чистая прибыль – 30 млн руб.',
        why='CNews: финансы предмета сделки, поле было пустым',
    ),
    dict(
        id='gb4fad654', field='eco.share', old='—',
        new='Партнёры рассчитывают в ближайшие 3–5 лет нарастить '
            'совокупную долю в трансграничном e-commerce до 42%.',
        quote='Партнёры рассчитывают в ближайшие 3–5 лет нарастить '
              'совокупную долю в трансграничном e-commerce до 42%.',
        why='ecomhub.ru: плановая цель партнёрства по доле рынка, поле '
            'было пустым',
    ),
    dict(id='gb4fad654', field='src', old=None,
         new=['CNews', 'https://www.cnews.ru/news/top/2025-09-25_mezhdunarodnaya_chast_kuplennoj'],
         quote='с августа 2025 г. BXB полностью принадлежит АО '
               '«Инвестсервис», гендиректор которого Сергей Сотник '
               'возглавил BXB',
         why='продавец предмета сделки и финансы предмета'),
    dict(id='gb4fad654', field='src', old=None,
         new=['cse.ru (пресс-релиз покупателя)', 'https://www.cse.ru/mow/news/kse-vykupil-kompaniyu-bxb/'],
         quote='Начала свою деятельность в 2017 году в странах СНГ и '
               'дальнего зарубежья как международное направление '
               'компании Boxberry и стала полностью автономной в 2025 '
               'году.',
         why='история бренда BXB'),
    dict(id='gb4fad654', field='src', old=None,
         new=['ecomhub.ru', 'https://ecomhub.ru/cse-acquisition-bxb-boxberry-international-delivery-crossborder-ecommerce/'],
         quote='Партнёры рассчитывают в ближайшие 3–5 лет нарастить '
               'совокупную долю в трансграничном e-commerce до 42%.',
         why='источник плановой цели по доле рынка'),
]
