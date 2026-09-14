# -*- coding: utf-8 -*-
"""Карточка `gbeb0dfe8` (Экспобанк/СДМ-банк, закрыта 11 сентября 2026) несла
`eco.context` с фразой «Кто именно продал контрольный пакет сейчас,
источники не называют» — приток 14 сентября нашёл слабое (по словам
заголовка) совпадение с mergers.ru, который называет продавцов прямо, со
ссылкой на материалы самого СДМ-банка.

Источник (кэш `data/inbox/raw/2026-09-14-articles.jsonl`,
`fetch_article_texts.py`):
https://mergers.ru/news/Jekspobank-priobrjol-kontrolnyj-paket-akcij-SDM-Banka-87507

Запуск: python3 pipeline/ingest/review.py [--write]
"""

MERGERS_URL = ('https://mergers.ru/news/Jekspobank-priobrjol-kontrolnyj-'
               'paket-akcij-SDM-Banka-87507')

QUOTE_SELLER = (
    'свою долю более чем в 15,5% продал один из его основателей основных '
    'владельцев банка Анатолий Ландсман, а также компания «Милавер рус», '
    'владевшая 53% акций'
)

FIXES = [
    dict(id='gbeb0dfe8', field='seller', old=None,
         new='Анатолий Ландсман, «Милавер рус»',
         quote=QUOTE_SELLER,
         why='mergers.ru называет продавцов прямо со ссылкой на материалы СДМ-банка'),
    dict(id='gbeb0dfe8', field='src', old=None,
         new=['Mergers.ru', MERGERS_URL],
         quote=QUOTE_SELLER,
         why='источник, впервые назвавший продавцов'),
]
