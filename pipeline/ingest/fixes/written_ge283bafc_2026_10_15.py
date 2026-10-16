# -*- coding: utf-8 -*-
"""Текст карточки ge283bafc, написанный по фактам (write_card.py, WRITING_BRIEF.md).

Запуск: python3 pipeline/ingest/review.py --write
"""

FIXES = [{'id': 'ge283bafc',
  'field': 'eco.context',
  'old': 'В сделку вошли четыре объекта общей площадью 18,2 тысячи квадратных метров в Москве и '
         'Санкт-Петербурге: Multispace Dinamo, Multispace Tverskaya, Multispace Pravda и '
         'Multispace Dubinin’Sky.',
  'new': 'Сделка охватывает четыре объекта общей площадью 18,2 тыс. кв. м в Москве и Петербурге. '
         'Это Multispace Pravda, Multispace Dinamo, Multispace Dubinin’Sky и Multispace Tverskaya.',
  'quote': 'В сделку вошли четыре объекта общей площадью 18,2 тысячи квадратных метров в Москве и '
           'Санкт-Петербурге … Multispace Dinamo, Multispace Tverskaya, Multispace Pravda и '
           'Multispace Dubinin’Sky',
  'why': 'текст написан по фактам 1, 2 (WRITING_BRIEF.md)'}]
