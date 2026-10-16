# -*- coding: utf-8 -*-
"""Текст карточки ged59a2eb, написанный по фактам (write_card.py, WRITING_BRIEF.md).

Запуск: python3 pipeline/ingest/review.py --write
"""

FIXES = [{'id': 'ged59a2eb',
  'field': 'eco.rationale',
  'old': 'Southern Sea Investment LLC выступила якорным инвестором и не является прямым '
         'покупателем доли в российской компании.',
  'new': 'По неофициальным данным, Southern Sea Investment LLC — якорный инвестор, а долю в '
         'российской компании напрямую не покупала.',
  'quote': 'Southern Sea Investment LLC выступила якорным инвестором и не является прямым '
           'покупателем доли в российской компании',
  'why': 'текст написан по фактам 1 (WRITING_BRIEF.md)'}]
