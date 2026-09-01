# -*- coding: utf-8 -*-
"""Почасовой приток 1 сентября 2026 (19:20 МСК) — четвёртый независимый
источник по уже опубликованной сделке `g2c27516d` (Аэрофлот выкупил
49% «Аэромара» у структуры Lufthansa). RB.ru дал факт, которого не было
ни в одном из трёх уже привязанных источников: немецкая доля в
«Аэромаре» шла не напрямую от Lufthansa, а через СП LSG Sky Chefs
(Lufthansa Service Holding + канадская Onex Food Service).

Запуск: python3 pipeline/ingest/review.py --write
"""

FIXES = [
    dict(id='g2c27516d', field='src', old=None,
         new=['RB.ru', 'https://rb.ru/news/aeroflot-vykupil-vse-akcii-proizvoditelya-bortovogo-pitaniya-aeromar-ranee-perevozchik-vladel-51-kompanii/'],
         quote='Компания «Аэромар» появилась в 1989 году как совместный проект '
               'СССР и США. Контрольный пакет в размере 51% получил ЦУ МВС '
               '«Аэрофлот», остальные 49% акций принадлежали «Марриотт '
               'Инфлайт Сервисиз», дочерней структуре гостиничной сети '
               '«Марриот». В 1996 году американского партнера сменила LSG '
               'Sky Chefs — совместное предприятие Lufthansa Service '
               'Holding и канадской Onex Food Service.',
         why='четвёртый источник — история создания «Аэромара» и структура прихода доли Lufthansa через LSG Sky Chefs'),
]
