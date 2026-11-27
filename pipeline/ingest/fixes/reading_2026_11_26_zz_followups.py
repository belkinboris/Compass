# -*- coding: utf-8 -*-
"""Вычитка 26 ноября 2026, доводка после партий: статус и заголовок Oerlikon по
годовому отчету группы за 2022 год (договор подписан 1 июня 2022 года, три
российские компании проданы) — правка law.struct из партии day_14 без них
спорила бы со статусом «Подписана». Запуск: python3 pipeline/ingest/review.py --write
"""

CARDS = ['gd0af0377', 'gfe5d2f94']

_Q = ('During the financial year 2022, the following significant changes in the Group structure occurred: '
      'Sale of subsidiaries On June 1, 2022 Oerlikon signed a contract for the sale of all subsidiaries in Russia '
      'to the local management. Consequently, Oerlikon OSS CIS LLC, Oerlikon Rus LLC and OOO Oerlikon Balzers Rus '
      'have been sold.')

FIXES = [
    {'id': 'gd0af0377', 'field': 'status', 'old': 'Подписана', 'new': 'Закрыта', 'quote': _Q,
     'why': 'годовой отчет Oerlikon за 2022 год: российские дочерние компании проданы'},
    {'id': 'gd0af0377', 'field': 'title', 'old': 'Местные руководители покупают российский бизнес Oerlikon',
     'new': 'Местные руководители купили российский бизнес Oerlikon', 'quote': _Q,
     'why': 'сделка закрыта — заголовок в прошедшем времени (title_standard, M&A/Закрыта)'},
    {'id': 'gd0af0377', 'field': 'date', 'old': '2022-06-02', 'new': '2022-06-01', 'quote': _Q,
     'why': 'день подписания договора по годовому отчету Oerlikon'},
    {'id': 'gfe5d2f94', 'field': 'law.appr', 'old': '—',
     'new': 'Допэмиссию 11 млн акций для мотивации сотрудников одобрил совет директоров МКПАО «Яндекс».',
     'quote': 'Совет директоров МКПАО "Яндекс" одобрил размещение 11 млн обыкновенных акций для программы долгосрочной мотивации сотрудников - около 2,8% уставного капитала.',
     'url': 'https://www.comnews.ru/content/247621/2026-09-30/2026-w40/1007/svoi-sredi-chuzhikh-yandeks-vypustit-11-mln-akciy-dlya-sotrudnikov',
     'why': 'одобрение совета директоров стояло только в контексте при пустых «Согласованиях» (test_approval_is_not_left_in_prose)'},
]
