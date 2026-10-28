# -*- coding: utf-8 -*-
"""Дневной уровень дочитывания 28 октября 2026: gc7143483 («Фригохолд» /
«Фриголайн Евразия», бывший российский бизнес Frigoglass). Полный обыск
саб-агентом нашёл условие сделки (обязательная скидка и налог на выход по
российским правилам для такой сделки) в уже привязанном источнике — не
было перенесено при первой записи.

Запуск: python3 pipeline/ingest/review.py gc7143483 --mark-deep --write
"""

FIXES = [
    {'id': 'gc7143483', 'field': 'src',
     'old': [['Abireg.ru', 'https://abireg.ru/newsitem/118849-kompaniya-glavy-emc-yanovskogo-stala-vladeltsem-orlovskogo-zavoda-frigolayn-evraziya/'],
             ['Milbank LLP', 'https://www.milbank.com/en/news/milbank-advises-frigoglass-in-connection-with-sale-of-its-russian-refrigeration-business.html']],
     'new': ['refindustry.com', 'https://refindustry.com/news/market-news/frigoglass-group-agrees-to-sell-russian-subsidiary-pending-approvals/'],
     'quote': 'The purchase price will be adjusted according to Russian regulatory requirements, '
              'including a mandatory 60% discount on the appraised value and significant exit taxes '
              'payable by the buyer.',
     'why': 'источник условия сделки о скидке и налоге на выход'},
    {'id': 'gc7143483', 'field': 'law.terms',
     'old': '—',
     'new': 'Цену сделки скорректировали по российским правилам для таких сделок: обязательная '
            '60-процентная скидка от оценочной стоимости актива, плюс заметный налог на выход, который '
            'платит покупатель.',
     'quote': 'The purchase price will be adjusted according to Russian regulatory requirements, '
              'including a mandatory 60% discount on the appraised value and significant exit taxes '
              'payable by the buyer.',
     'why': 'условие сделки (скидка и налог на выход) было в источнике refindustry.com, не перенесено '
            'при первой записи'},
]
