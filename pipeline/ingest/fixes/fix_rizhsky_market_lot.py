# -*- coding: utf-8 -*-
"""Карточка `ge1b2eba1` (участок с Рижским рынком, аукцион) — поля
дословными цитатами из прочитанного полного текста RB.RU.

Источник: https://rb.ru/news/rizhskij-cvetochnyj-rynok-vystavyat-na-torgi-nachalnaya-stoimost-lota-155-mln-rublej/

Запуск: python3 pipeline/ingest/review.py [--write]
"""

QUOTE_CONTEXT = (
    'Расположенные на участке здания, включая рынок и универмаг, нужно '
    'будет снести или реконструировать.'
)

QUOTE_SHARE = (
    'Территория расположена на проспекте Мира. Право заключить договор о '
    'её комплексном развитии планируют разыграть на электронном аукционе.'
)

QUOTE_VAL = (
    'Начальная цена лота составляет 155,4 млн рублей, шаг аукциона — 3,1 '
    'млн рублей, или 2% от стартовой стоимости. Для участия в торгах '
    'потребуется внести задаток в размере 31,1 млн рублей — 20% от '
    'начальной цены.'
)

QUOTE_TERMS = (
    'К участникам также предъявят требования по опыту: за последние пять '
    'лет они должны были участвовать в строительстве объектов общей '
    'площадью не менее 17 тыс. кв. м.'
)

QUOTE_STRUCT = (
    'Аукцион должен быть организован и проведён не позднее чем через 90 '
    'дней после получения документов.'
)

FIXES = [
    dict(id='ge1b2eba1', field='eco.context', old='—',
         new=QUOTE_CONTEXT, quote=QUOTE_CONTEXT,
         why='что будет с постройками на участке'),
    dict(id='ge1b2eba1', field='eco.share', old='—',
         new=QUOTE_SHARE, quote=QUOTE_SHARE,
         why='где участок и что именно продают — право на КРТ'),
    dict(id='ge1b2eba1', field='eco.val', old='—',
         new=QUOTE_VAL, quote=QUOTE_VAL,
         why='цена лота, шаг аукциона и задаток'),
    dict(id='ge1b2eba1', field='law.terms', old='—',
         new=QUOTE_TERMS, quote=QUOTE_TERMS,
         why='требования к участникам торгов'),
    dict(id='ge1b2eba1', field='law.struct', old='—',
         new=QUOTE_STRUCT, quote=QUOTE_STRUCT,
         why='срок проведения аукциона'),
]
