# -*- coding: utf-8 -*-
"""Качество, 8 октября 2026 (ежедневный прогон 21:37 МСК) — недельная и
месячная очередь дочитывания.

Запуск:
    python3 pipeline/ingest/review.py [--write]
"""

QUOTE_PRIOSKOLYE_FIN = (
    'Чистый убыток ООО «Инвест Трейд» за 2024 год составил 31.948 млн руб.'
)

QUOTE_PRIOSKOLYE_ARREST = (
    'Один из собеседников "Ъ" на рынке говорит, что акции «Приосколья» '
    'сейчас арестованы.'
)

QUOTE_MEGA_RATIONALE = (
    'Новым генеральным директором УК «Мега» была назначена Оксана '
    'Козлова, которая свыше 10 лет проработала в компании. Любовь '
    'Попова перейдет в группу «Газпромбанк» и займется развитием '
    'портфеля коммерческой недвижимости и других проектов, находящихся '
    'под управлением группы.'
)

QUOTE_RCF_FIN_2024 = (
    'Выручка ООО РЧФ в 2024 году составила 743,1 млн руб., чистая '
    'прибыль — 118,5 млн руб.'
)

QUOTE_NORNICKEL_BELAZ_PUTIN = (
    'В июле 2026 года председатель правления «Норникеля» Владимир '
    'Потанин на встрече с Президентом России Владимиром Путиным '
    'проинформировал о сотрудничестве с белорусскими партнерами. Тогда '
    'он сообщил, что вместе с компанией «БЕЛАЗ» приступили к программе '
    'создания горной техники нового поколения.'
)

QUOTE_LIME_NONDISCLOSURE = (
    'Представитель НМГ подтвердил факт сделки, но не раскрыл размер '
    'приобретенной доли, юридическое лицо и сумму сделки.'
)

FIXES = [
    dict(id='gcb875d9e', field='src', old=None,
         new=['Коммерсантъ', 'https://www.kommersant.ru/doc/7433611'],
         quote=QUOTE_PRIOSKOLYE_ARREST,
         why='недельная очередь 08.10.2026: вторая заметка Коммерсанта, '
             'упоминает арест акций — отдельно от уже привязанной'),
    dict(id='gcb875d9e', field='src', old=None,
         new=['АК&М', 'https://www.akm.ru/news/agrokompleks_tkacheva_kupil_invest_treyd/'],
         quote=QUOTE_PRIOSKOLYE_FIN,
         why='недельная очередь 08.10.2026: финансы «Инвест Трейд» за '
             '2024 год — АК&М'),
    dict(id='gcb875d9e', field='eco.target_fin', old='—',
         new=QUOTE_PRIOSKOLYE_FIN, quote=QUOTE_PRIOSKOLYE_FIN,
         why='недельная очередь 08.10.2026: финансы покупателя «Инвест '
             'Трейд» за 2024 год — АК&М'),
    dict(id='gaec5231e', field='src', old=None,
         new=['Retail.ru', 'https://www.retail.ru/news/gazprombank-peredal-upravlenie-torgovymi-tsentrami-mega-kompanii-veles-menedzhme-5-noyabrya-2025-271020/'],
         quote=QUOTE_MEGA_RATIONALE,
         why='месячная очередь 08.10.2026: прямая цитата зампреда '
             'Газпромбанка о причине передачи и смена гендиректора УК — Retail.ru'),
    dict(id='gaec5231e', field='eco.rationale', old='—',
         new=QUOTE_MEGA_RATIONALE, quote=QUOTE_MEGA_RATIONALE,
         why='месячная очередь 08.10.2026: смена гендиректора УК «Мега» '
             'одновременно с передачей управления — Retail.ru'),
    dict(id='g672c6dfe', field='eco.target_fin', old='—',
         new=QUOTE_RCF_FIN_2024, quote=QUOTE_RCF_FIN_2024,
         why='месячная очередь 08.10.2026: финансы самой РЧФ за 2024 '
             'год — Коммерсантъ (уже в src)'),
    dict(id='g2b1ff5cb', field='src', old=None,
         new=['Советская Белоруссия', 'https://www.sb.by/articles/svyazuyushchee-zveno-tekhnologicheskogo-suvereniteta.html'],
         quote=QUOTE_NORNICKEL_BELAZ_PUTIN,
         why='месячная очередь 08.10.2026: технические подробности СП и '
             'новый спикер (гендиректор-конструктор БЕЛАЗа) — sb.by'),
    dict(id='g2b1ff5cb', field='law.struct', old='—',
         new=QUOTE_NORNICKEL_BELAZ_PUTIN, quote=QUOTE_NORNICKEL_BELAZ_PUTIN,
         why='месячная очередь 08.10.2026: о проекте докладывали '
             'президенту РФ за два месяца до подписания — sb.by'),
    dict(id='g29d31edd', field='src', old=None,
         new=['Sostav.ru', 'https://www.sostav.ru/publication/nmg-voshla-v-ustavnyj-kapital-kompanii-vladeltsa-biletnoj-sistemy-lajm-86757.html'],
         quote=QUOTE_LIME_NONDISCLOSURE,
         why='недельная очередь 08.10.2026: явный отказ стороны '
             'раскрывать долю/сумму — Sostav.ru'),
    dict(id='g29d31edd', field='eco.share', old='—',
         new=QUOTE_LIME_NONDISCLOSURE, quote=QUOTE_LIME_NONDISCLOSURE,
         why='недельная очередь 08.10.2026: нераскрытие — осознанный '
             'отказ стороны, не пробел источников — Sostav.ru'),
]
