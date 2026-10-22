# -*- coding: utf-8 -*-
"""Карточка g09baae21 (Аргумент-Байт/«Созидательный венчур»): второй источник
того же факта (Mergers.ru) — все числа (5,46%, Митин 82,66%, Пустовой 5%)
уже есть в карточке, новых фактов не добавляет.

Запуск: python3 pipeline/ingest/review.py --write
"""

FIXES = [{'id': 'g09baae21',
  'field': 'src',
  'old': [['Телеграм-канал: Русский Венчур', 'https://t.me/rusven/7803']],
  'new': ['Mergers.ru',
          'https://mergers.ru/news/Fond-Sozidatelnyj-venchur-vlozhilsya-v-razrabotchika-'
          'korporativnoj-platformy-dannyh-ANG-Platform-87675'],
  'quote': 'Инвестиционное товарищество «Созидательный венчур» стало владельцем доли в размере '
           '5,46% в ООО «Аргумент-Байт».',
  'why': 'enrich.py нашёл второй источник (дружный прогон, 22 октября 2026) — факты совпадают, '
         'ничего нового'}]
