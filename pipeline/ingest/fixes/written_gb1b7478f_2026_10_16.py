# -*- coding: utf-8 -*-
"""Текст карточки gb1b7478f, написанный по фактам (write_card.py, WRITING_BRIEF.md).

Запуск: python3 pipeline/ingest/review.py --write
"""

FIXES = [{'id': 'gb1b7478f',
  'field': 'eco.context',
  'old': 'По информации компании от января 2023 года, 22,68% HeadHunter Group PLC принадлежит '
         'Kismet Capital Group (KCG) Ивана Таврина, около 10% компании были проданы ему структурой '
         'Elbrus Capital за неустановленную сумму.',
  'new': 'По данным самой компании, на январь 2023 года 22,68% HeadHunter Group PLC принадлежало '
         'Kismet Capital Group (KCG) Ивана Таврина. Из этого пакета примерно 10% акций HeadHunter '
         'Group PLC Таврин купил у структуры Elbrus Capital; цена не установлена.',
  'quote': 'По информации компании от января 2023 года, 22,68% HeadHunter Group PLC принадлежит '
           'Kismet Capital Group (KCG) Ивана Таврина … около 10% компании были проданы ему '
           'структурой Elbrus Capital за неустановленную сумму',
  'why': 'текст написан по фактам 1, 2 (WRITING_BRIEF.md)'}]
