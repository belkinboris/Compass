# -*- coding: utf-8 -*-
"""Карточка g6a917c05: сумма и доля на «Обзоре» (`sum`/заголовок) не
попали на «Экономист» — `eco.sum`/`eco.share` остались «—». Одно и то же
значение, docs/card_money.md («sum и eco.sum — одно значение»); найдено
test_audit_queue.py::test_the_sum_on_the_overview_is_the_sum_in_the_economist.

Запуск: python3 pipeline/ingest/review.py --write
"""

FIXES = [{'id': 'g6a917c05',
  'field': 'eco.sum',
  'old': '—',
  'new': '3 млн ₽',
  'quote': 'Венчурный фонд brainbox_I проинвестировал 3 млн рублей в сервис ИИ-контента '
           'Givon AI за 4%',
  'why': 'то же число, что в sum («Обзор»); docs/card_money.md — поля ведутся одним значением'},
 {'id': 'g6a917c05',
  'field': 'eco.share',
  'old': '—',
  'new': '4%',
  'quote': 'Венчурный фонд brainbox_I проинвестировал 3 млн рублей в сервис ИИ-контента '
           'Givon AI за 4%',
  'why': 'доля из заголовка, подтверждённого притоком при заведении карточки'}]
