# -*- coding: utf-8 -*-
"""gf2b5f78c (Муслюмовский участок недр, Башкирия): сумма в «Финансах».
Сумма на «Обзоре» — стартовая цена аукциона; та же цифра обязана быть в
финансовом разделе (test_the_sum_on_the_overview_is_the_sum_in_the_economist).

Запуск: python3 pipeline/ingest/review.py --write
"""

QUOTE_SUM = 'Стартовая цена — 200,3 миллионов рублей. Шаг аукциона — 20,3 миллионов рублей.'

FIXES = [
 {'id': 'gf2b5f78c',
  'field': 'eco.sum',
  'old': '—',
  'new': '200,3 млн ₽',
  'quote': QUOTE_SUM,
  'why': 'та же сумма, что на «Обзоре» (стартовая цена аукциона; facts.price.meaning = auction_start)'},
]
