# -*- coding: utf-8 -*-
"""Глубокая ревизия 2025 (партия 11), карточки 86–100 из «сотки».

Все 15 карточек — «обыскано под 12 углов, больше ничего не нашлось».

Находки:
  g8e78bbb2 (Scandic Construction): +src ErmolaevV.ru.
  g69437311 (Воображариум / Простые правила): +src Sostav.ru.
  g68ebf773 (ВсеИнструменты.ру IPO): +src Interfax.
  g8cbf31b0 (Merlion / VITEK+Maxwell): +src Sostav.ru.
  gf577d893 (СДЭК / СФН): +src Interfax.
  gf6be51a1 (Ростелеком Армения / Viva): +src Abireg.ru.
  gfe21a083 (Валента Фарм / Опека): +src Vademecum.
  gaa59d3a1 (земельные активы): +src ГородN.ru.
  g507c9a35, g62cbdd8b, ga80371a8, g428f6180,
  gd96d269e, g4b447867, g5190658a: только deep_researched.
"""

FIXES = [
    # === g8e78bbb2: Scandic Construction / завод в Ленобласти ===
    # ErmolaevV.ru подтверждает продажу завода в Ленобласти.
    dict(id='g8e78bbb2', field='src', old=None,
         new=['ErmolaevV.ru',
              'https://ermolaevv.ru/tpost/rszmi0r651-prodan-zavod-scandic-'
              'construction-v-leni'],
         quote='Продан завод Scandic Construction в Ленинградской области '
               'по производству готовы',
         why='отраслевой ресурс по стройматериалам подтверждает факт продажи '
             'завода и географию; скачан и сверен'),

    # === g69437311: Воображариум / Простые правила ===
    # Sostav.ru подтверждает покупку издателем «Имаджинариума» компании «Простые правила».
    dict(id='g69437311', field='src', old=None,
         new=['Sostav.ru',
              'https://www.sostav.ru/publication/izdatel-imadzhinariuma-kupil-'
              'kompaniyu-prostye-pravila-69652.html'],
         quote='издатель «Имаджинариума» купил компанию «Простые правила»',
         why='Sostav.ru раскрывает имена сторон и предмет сделки; '
             'скачан и сверен'),

    # === g68ebf773: ВсеИнструменты.ру / IPO ===
    # Interfax подтверждает анонс IPO ВсеИнструменты.ру на МосБирже.
    dict(id='g68ebf773', field='src', old=None,
         new=['Interfax', 'https://www.interfax.ru/business/967778'],
         quote='онлайн-ритейлер «ВсеИнструменты.ру» анонсировал IPO на '
               'Московской бирже',
         why='Interfax фиксирует официальный анонс IPO с параметрами; '
             'скачан и сверен'),

    # === g8cbf31b0: Merlion / VITEK и Maxwell ===
    # Sostav.ru подтверждает выкуп Merlion владельца брендов VITEK и Maxwell.
    dict(id='g8cbf31b0', field='src', old=None,
         new=['Sostav.ru',
              'https://www.sostav.ru/publication/postavshchik-elektroniki-merlion-'
              'vykupil-vladeltsa-brendov-vitek-i-maxwell-68703.html'],
         quote='поставщик электроники Merlion выкупил владельца брендов Vitek '
               'и Maxwell',
         why='Sostav детализирует предмет сделки (бренды VITEK, Maxwell); '
             'скачан и сверен'),

    # === gf577d893: СДЭК / фонд СФН ===
    # Interfax подтверждает продажу 55% СДЭК основателем фонду УК «СФН».
    dict(id='gf577d893', field='src', old=None,
         new=['Interfax', 'https://www.interfax.ru/business/969410'],
         quote='основатель СДЭК продал 55% компании фонду под управлением УК «СФН»',
         why='Interfax фиксирует долю и покупателя — детали, отсутствующие '
             'в Telegram-источнике; скачан и сверен'),

    # === gf6be51a1: Ростелеком Армения / Viva ===
    # Abireg.ru подтверждает одобрение КРОУ сделки по продаже GNC-Alfa.
    dict(id='gf6be51a1', field='src', old=None,
         new=['Abireg.ru', 'https://abireg.ru/newsitem/107902/'],
         quote='«Ростелеком» выходит из Армении: КРОУ одобрила продажу '
               'GNC-Alfa компании Viva Армения',
         why='армянское бизнес-издание раскрывает одобрение регулятора '
             'и официальное имя покупателя; скачан и сверен'),

    # === gfe21a083: Валента Фарм / Опека ===
    # Vademecum подтверждает выкуп основателем доли Валента Фарм в «Опеке».
    dict(id='gfe21a083', field='src', old=None,
         new=['Vademecum',
              'https://vademec.ru/news/2024/10/31/aktsionery-valenty-farm-prodali-'
              'svoi-doli-v-seti-opeka-ee-osnovatelyu/'],
         quote='акционеры «Валента Фарм» продали свои доли в сети «Опека» '
               'ее основателю',
         why='профильное фармацевтическое издание раскрывает структуру сделки '
             '(основатель выкупил доли ФА); скачан и сверен'),

    # === gaa59d3a1: Слияние земельных просторов ===
    # Город N (Ростов) подтверждает сделку по земельным активам.
    dict(id='gaa59d3a1', field='src', old=None,
         new=['Город N',
              'https://gorodn.ru/razdel/novosti_kompaniy/sdelki/sliyanie-zemelnykh-prostorov/'],
         quote='Слияние земельных просторов',
         why='ростовский деловой портал с первичной публикацией о сделке; '
             'скачан и сверен'),
]
