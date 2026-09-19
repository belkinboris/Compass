# -*- coding: utf-8 -*-
"""Карточка `g7a96dda2` («Трамплин Холдинг»/Malt System) — mergers.ru
(перепечатка CNews, кэш `data/inbox/raw/2026-09-14-articles.jsonl`) назвал
мотив сделки прямой цитатой Malt System и уточнил долю, оставшуюся у
продавца, — этого не было в источниках, на которых карточка собиралась.

Источник: https://mergers.ru/news/Vladelcy-razrabotchika-processora-Irtysh-
kupili-kontrolnuyu-dolyu-v-rossijskom-dizajn-centre-87513

Запуск: python3 pipeline/ingest/review.py [--write]
"""

MERGERS_URL = (
    'https://mergers.ru/news/Vladelcy-razrabotchika-processora-Irtysh-'
    'kupili-kontrolnuyu-dolyu-v-rossijskom-dizajn-centre-87513'
)

QUOTE_RATIONALE = (
    'Как сообщили CNews в Malt, цель сделки — стать значимым и '
    'стратегически важным коммерческим разработчиком уникальных '
    'наукоёмких электронных и фотонных специализированных блоков, '
    'интегральных микросхем и сложных приборов в России и странах '
    'Глобального Юга, опираясь на собственные разработки компании от '
    'идеи до чипа, отечественную научную школу и кооперацию с партнерами.'
)

QUOTE_STAKE = (
    'Эту долю компания выкупила у основателя дизайн-центра Сергея '
    'Елизарова, теперь ему принадлежит 39%.'
)

FIXES = [
]
