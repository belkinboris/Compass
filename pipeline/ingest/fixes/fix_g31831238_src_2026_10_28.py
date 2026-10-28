# -*- coding: utf-8 -*-
"""Карточка g31831238 (Intel/Classiq): шаг 8 притока — дополнительные
источники, найденные и скачанные поиском (`fetch_article_texts.py --write`),
помимо изначально привязанного incrussia.ru."""

_OLD_SRC = [['Inc. Russia', 'https://incrussia.ru/news/intel-kupit-razrabotchika-po-dlya-kvantovyh-kompyuterov-classiq-za-2-3-mlrd/']]

FIXES = [
    {'id': 'g31831238', 'field': 'src', 'old': _OLD_SRC,
     'new': ['Intel / Business Wire', 'https://finance.yahoo.com/technology/ai/articles/intel-acquire-classiq-create-full-203000273.html'],
     'quote': 'Intel Corporation today announced that it has entered into a definitive agreement to acquire Classiq',
     'why': 'официальный пресс-релиз Intel о сделке'},
    {'id': 'g31831238', 'field': 'src', 'old': _OLD_SRC,
     'new': ['Ynetnews (Calcalist)', 'https://www.ynetnews.com/business/article/rkd8qnanme'],
     'quote': 'Intel is acquiring Israeli quantum computing startup Classiq for $2.3 billion in a combination of cash and shares',
     'why': 'самый подробный материал: финансы Classiq, доли сотрудников, конфликт интересов CEO Intel'},
    {'id': 'g31831238', 'field': 'src', 'old': _OLD_SRC,
     'new': ['Calcalist', 'https://www.calcalistech.com/ctechnews/article/psr5mmhcl'],
     'quote': 'On Monday, Intel announced that it would acquire Classiq for $2.3 billion in cash and stock',
     'why': 'интервью с CEO Classiq Ниром Минерби'},
    {'id': 'g31831238', 'field': 'src', 'old': _OLD_SRC,
     'new': ['Hardware Busters', 'https://hwbusters.com/news/intels-classiq-acquisition-gives-its-silicon-qubits-a-software-stack-for-a-reported-2-3-billion/'],
     'quote': 'The company is small. Bloomberg puts its headcount at about 130, says it has raised more than $200 million, and names BMW and AT&T among its customers.',
     'why': 'техническая сторона сделки (кубиты Intel, клиенты Classiq)'},
    {'id': 'g31831238', 'field': 'src', 'old': _OLD_SRC,
     'new': ['Cryptopolitan', 'https://www.cryptopolitan.com/intel-buys-quantum-software-firm-classiq/'],
     'quote': "Tan's own ties run through the quantum field. Before Intel, he ran Cadence Design Systems and chairs Walden International.",
     'why': 'инвестиционная история Лип-Бу Тана в квантовом секторе, контекст распродажи активов Intel'},
    {'id': 'g31831238', 'field': 'src', 'old': _OLD_SRC,
     'new': ['Jerusalem Post', 'https://www.jpost.com/business-and-innovation/article-913011'],
     'quote': 'Globes reported that Intel acquired Classiq for $2.2 billion, making it Intel\'s largest acquisition in Israel since the 2017 purchase of Mobileye for $15.3 billion.',
     'why': 'альтернативная оценка суммы ($2,2 млрд по Globes), комментарий Team8'},
]
