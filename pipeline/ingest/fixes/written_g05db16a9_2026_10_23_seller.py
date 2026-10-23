# -*- coding: utf-8 -*-
"""Карточка g05db16a9: продавец найден (обязательный поиск для продажи с
торгов, docs/card_parties.md) — коллекция семьи Шлюмберже, подтверждено
названием самих торгов Sotheby's («Le Temps Retrouvé: The Schlumberger
Collection», sothebys.com) и совпадает с тем, что пишет источник.

Запуск: python3 pipeline/ingest/review.py --write
"""

FIXES = [{'id': 'g05db16a9',
  'field': 'seller',
  'old': None,
  'new': 'Семья Шлюмберже',
  'quote': 'Оно не покидало парижский особняк семьи Шлюмберже, и знали его '
           'только по черно-белой фотографии.',
  'why': 'продавец для продажи с торгов обязателен (docs/card_parties.md); '
         'подтверждено названием торгов Sotheby\'s "Le Temps Retrouvé: The '
         'Schlumberger Collection"'}]
