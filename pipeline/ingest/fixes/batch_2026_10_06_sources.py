# -*- coding: utf-8 -*-
"""Качество, 6 октября 2026 — первоисточник вместо агрегатора (шаг 7в).

Пять карточек, у которых единственным источником был mergers.ru (сам
пересказывает чужую заметку), получили настоящий первоисточник:
Коммерсантъ (gmru-sucden-poetti, gmru-mirgorodsky-nattys), CNews
(gmru-voshod-voronezh-rocket — у топ-изданий об этом конкретном раунде
на 100 млн ₽ текста не нашлось, только про более ранние раунды), АК&М
(gmru-razvitie-stroy-aktivov-akzo — информагентство, раньше любого
пересказа) и Ведомости (gmru-vim-poklonka).

Про gmru-sucden-poetti: Коммерсантъ описывает это как «фактически
получили контроль» через залог доли по товарному кредиту — то же самое,
что уже написано в law.struct карточки («передача в залог… обеспечение
по товарному кредиту»); расхождения с текстом карточки нет.

Запуск:
    python3 pipeline/ingest/review.py [--write]
"""

QUOTE_SUCDEN_POETTI = (
    'Структуры французского производителя сахара Sucden фактически '
    'получили контроль над компанией «Милфудс», выпускающей кофе Poetti '
    'и Milagro.'
)

QUOTE_NATTYS = (
    'Геннадий Миргородский в конце июня стал владельцем 70% в ООО '
    '«Нуттис» (бренд Nattys), следует из СПАРК.'
)

QUOTE_VORONEZH_ROCKET = (
    'Венчурный фонд «Восход» инвестировал 100 млн руб. в компанию ООО '
    '«3Д Исследования и разработки» — разработчика частной '
    'ракеты-носителя сверхлегкого класса «Воронеж».'
)

QUOTE_AKZO_NOBEL = (
    'Российские активы Akzo Nobel переданы во временное управление АО '
    '«Развитие строительных активов». Соответствующий указ, подписанный '
    'президентом РФ Владимиром Путиным, опубликован на портале правовой '
    'информации.'
)

QUOTE_VIM_POKLONKA = (
    'Фонд под управлением компании «ВИМ сбережения» (ранее « ВТБ капитал '
    'пенсионный резерв») ведет переговоры о приобретении делового '
    'квартала «Поклонка плейс», расположенного на Поклонной улице'
)

FIXES = [
    dict(id='gmru-sucden-poetti', field='src', old=None,
         new=['Коммерсантъ', 'https://www.kommersant.ru/doc/8815172'],
         quote=QUOTE_SUCDEN_POETTI,
         why='первоисточник вместо агрегатора 06.10.2026: mergers.ru '
             'пересказывал именно эту заметку Коммерсанта'),
    dict(id='gmru-mirgorodsky-nattys', field='src', old=None,
         new=['Коммерсантъ', 'https://www.kommersant.ru/doc/8814398'],
         quote=QUOTE_NATTYS,
         why='первоисточник вместо агрегатора 06.10.2026: mergers.ru '
             'пересказывал именно эту заметку Коммерсанта'),
    dict(id='gmru-voshod-voronezh-rocket', field='src', old=None,
         new=['CNews', 'https://www.cnews.ru/news/top/2026-07-14_rossijskij_milliarder_vlozhil'],
         quote=QUOTE_VORONEZH_ROCKET,
         why='первоисточник вместо агрегатора 06.10.2026: профильное '
             'издание написало об этом раунде на день раньше mergers.ru'),
    dict(id='gmru-razvitie-stroy-aktivov-akzo', field='src', old=None,
         new=['АК&М', 'https://www.akm.ru/news/v_putin_peredal_rossiyskie_aktivy_akzo_nobel_vo_vremennoe_upravlenie_kompanii_razvitie_stroitelnykh_/'],
         quote=QUOTE_AKZO_NOBEL,
         why='первоисточник вместо агрегатора 06.10.2026: информагентство '
             'сообщило об указе в день его публикации'),
    dict(id='gmru-vim-poklonka', field='src', old=None,
         new=['Ведомости', 'https://www.vedomosti.ru/realty/articles/2026/07/06/1211350-bivshaya-struktura-vtb-mozhet-zakrit-odnu-iz-krupneishih-sdelok'],
         quote=QUOTE_VIM_POKLONKA,
         why='первоисточник вместо агрегатора 06.10.2026: mergers.ru '
             'пересказывал именно эту заметку Ведомостей'),
]
