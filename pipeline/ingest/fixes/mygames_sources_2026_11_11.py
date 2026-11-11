# -*- coding: utf-8 -*-
"""Карточка gb3029360 (My.Games / Александр Чачава, MBO 2026): дополнительные
источники, найденные саб-агентом (шаг 8 притока) сверх Коммерсанта.

Запуск: python3 pipeline/ingest/review.py gb3029360 --write
"""

FIXES = [
    {'id': 'gb3029360', 'field': 'src', 'old': None,
     'new': ['Playground.ru', 'https://www.playground.ru/misc/news/rukovodstvo_my_games_vykupilo_kompaniyu_u_aleksandra_chachavy_pri_podderzhke_investora_iz_oae-1889474'],
     'quote': 'Издатель и разработчик видеоигр MY.GAMES официально объявил о процедуре выкупа компании собственным менеджментом.',
     'why': 'единственный найденный русскоязычный источник, который называет инвестора из ОАЭ по имени'},
    {'id': 'gb3029360', 'field': 'src', 'old': None,
     'new': ['PocketGamer.biz', 'https://www.pocketgamer.biz/mygames-agrees-to-management-buyout-backed-by-uae-investor/'],
     'quote': 'My.Games has signed a definitive agreement towards a management buyout from its sole shareholder, Alexander Chachava.',
     'why': 'независимое зарубежное отраслевое издание, подтверждает сделку и цитаты сторон'},
    {'id': 'gb3029360', 'field': 'src', 'old': None,
     'new': ['Mobilegamer.biz', 'https://mobilegamer.biz/my-games-management-agrees-uae-backed-buyout-from-owner-alexander-chachava/'],
     'quote': 'Chachava, managing partner of venture fund LETA Capital, bought My.Games from Russian tech company VK for $642m in September 2022.',
     'why': 'источник факта о венчурном фонде LETA Capital Чачавы'},
]
