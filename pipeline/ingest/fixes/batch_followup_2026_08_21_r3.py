# -*- coding: utf-8 -*-
"""Месячная очередь качества, 21 августа 2026, продолжение (после починки
заражения Sokolov): `g94683ed2` (Wildberries & Russ/«Рив Гош»).

Поиск источников: malls.ru даёт масштаб сети (250+ магазинов, 88
городов) — поле было пустой заглушкой.
"""

FIXES = [
    dict(id='g94683ed2', field='eco.share', old='—',
         new='Сейчас у сети более 250 магазинов в 88 городах.',
         quote='Сейчас у сети более 250 магазинов в 88 городах.',
         why='масштаб сети (предмет сделки) не был раскрыт вовсе'),
    dict(id='g94683ed2', field='src', old=None,
         new=['Malls.ru', 'https://www.malls.ru/rus/news/riv-gosh-'
              'ukhodit-k-wildberries-zachem-marketpleysu-250-magazinov-'
              'krasoty.shtml'],
         quote='Сейчас у сети более 250 магазинов в 88 городах.',
         why='новый источник — масштаб сети'),
]
