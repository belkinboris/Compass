# -*- coding: utf-8 -*-
"""Приток 24 сентября 2026 (16:20 МСК), g17fc21d6 («Ашан» не успел продать
российский бизнес «Кама Капиталу»): RETAILER.ru пересказывает уже
известный срыв сделки (сумма и оценки — те же 60/70 млрд ₽ от Бурмистрова
и Шумова, что уже в eco.val) и добавляет один новый факт — выручку
российского бизнеса за 2025 год со ссылкой на Infoline, которой в
карточке ещё не было (eco.target_fin стояло прочерком).

Источник: https://retailer.ru/sdelka-po-prodazhe-rossijskogo-auchan-sorvalas-posle-ukaza-o-vremennom-upravlenii/,
прочитан целиком, кэш в data/inbox/raw/2026-09-24-articles.jsonl.
Черновик d21470642 отпущен через raw_screen.py --enrich (не отдельная
карточка — та же сделка).

Запуск: python3 pipeline/ingest/review.py --write
"""

QUOTE_REVENUE = (
    'По данным Infoline, выручка российского бизнеса по итогам 2025 года '
    'составила 269,7 млрд руб., снизившись на 2,9%.'
)

FIXES = [
    dict(id='g17fc21d6', field='eco.target_fin', old='—', new=QUOTE_REVENUE,
         quote=QUOTE_REVENUE,
         why='приток 24.09.2026, источник RETAILER.ru со ссылкой на Infoline: выручка российского бизнеса Auchan за 2025 год, поле стояло прочерком'),
]
