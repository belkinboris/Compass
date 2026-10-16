# -*- coding: utf-8 -*-
"""Текст карточки g1e73548b, написанный по фактам (write_card.py, WRITING_BRIEF.md).

Запуск: python3 pipeline/ingest/review.py --write
"""

FIXES = [{'id': 'g1e73548b',
  'field': 'law.appr',
  'old': 'Покупка была одобрена правительственной комиссией РФ по контролю за осуществлением '
         'иностранных инвестиций.',
  'new': 'Сделку одобрила правкомиссия по контролю за иностранными инвестициями.',
  'quote': 'Покупка была одобрена правительственной комиссией РФ по контролю за осуществлением '
           'иностранных инвестиций.',
  'why': 'текст написан по фактам 1 (WRITING_BRIEF.md)'},
 {'id': 'g1e73548b',
  'field': 'law.struct',
  'old': 'Предприятие, ранее принадлежавшее французской Leoni Wiring Systems France (62,49%), а '
         'также немецким Leoni Bordnetz-Systeme GmbH (37,49%) и Leoni Bordnetze Verwaltungs GmbH '
         '(0,015%), с 28 февраля перешло под контроль нижегородского ООО «Импульс».',
  'new': '28 февраля контроль над заводом перешёл к нижегородскому ООО «Импульс». До этого у '
         'завода было три владельца из группы Leoni: Leoni Wiring Systems France (Франция) — '
         '62,49%, Leoni Bordnetz-Systeme GmbH (Германия) — 37,49% и Leoni Bordnetze Verwaltungs '
         'GmbH (Германия) — 0,015%.',
  'quote': 'ранее принадлежавшее французской Leoni Wiring Systems France (62,49%), а также '
           'немецким Leoni Bordnetz-Systeme GmbH (37,49%) и Leoni Bordnetze Verwaltungs GmbH '
           '(0,015%) … с 28 февраля перешло под контроль нижегородского ООО «Импульс».',
  'why': 'текст написан по фактам 2, 3 (WRITING_BRIEF.md)'}]
