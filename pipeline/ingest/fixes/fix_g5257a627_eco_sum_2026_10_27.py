# -*- coding: utf-8 -*-
"""Карточка g5257a627: сумма на «Обзоре» (509 млн ₽) не попала на
«Экономист» — `eco.sum` остался «—». Одно и то же значение,
docs/card_money.md («sum и eco.sum — одно значение»); найдено
test_audit_queue.py::test_the_sum_on_the_overview_is_the_sum_in_the_economist
после публикации карточки решением владельца 27 октября 2026.

Запуск: python3 pipeline/ingest/review.py --write
"""

FIXES = [{'id': 'g5257a627',
  'field': 'eco.sum',
  'old': '—',
  'new': '509 млн ₽',
  'quote': 'Нынешняя цена не стала новым повышением: до 509 млн рублей объект '
           'подорожал еще в ноябре 2025 года.',
  'why': 'то же число, что в sum («Обзор»); docs/card_money.md — поля ведутся одним значением'}]
