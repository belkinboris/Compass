# -*- coding: utf-8 -*-
"""Текст карточки g6d719087, написанный по фактам (write_card.py, WRITING_BRIEF.md).

Запуск: python3 pipeline/ingest/review.py --write
"""

FIXES = [{'id': 'g6d719087',
  'field': 'law.struct',
  'old': 'SIG Investments получила 25% в капитале компании, остальные 75% — у текущих акционеров.',
  'new': 'Нынешние акционеры сохраняют 75%, а SIG Investments получил 25% капитала.',
  'quote': 'SIG Investments получила 25% в капитале компании … остальные 75% — у текущих '
           'акционеров',
  'why': 'текст написан по фактам 1, 2 (WRITING_BRIEF.md)'}]
