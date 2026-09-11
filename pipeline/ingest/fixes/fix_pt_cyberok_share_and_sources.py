# -*- coding: utf-8 -*-
"""Карточка `gdc686ec2` (Positive Technologies / CyberOK, 11 сентября 2026) —
доля и источники, которых у нас не было, когда конкурент их уже показал.

ЧТО СЛУЧИЛОСЬ. Пост канала @dealsma (перепечатка «M&A Burakova», 11:24 МСК)
вышел раньше нашего (13:18 МСК) и назвал то, чего в нашей карточке не было:
33% акций, юрлицо АО «Сайбер ОК», выручку и убыток за 2025 год. Наша
карточка держалась на одном РБК; CNews лежал в hold-файле обогащения как
«слабое совпадение», и его никто не прочитал (разбор — CLAUDE.md, 11 сентября
2026, «Конкурент раньше и богаче»).

ИСТОЧНИКИ (все забраны в кэш `data/inbox/raw/2026-09-11-articles.jsonl`
`fetch_article_texts.py`, цитаты сверяются с ним дословно):
- Telesputnik, 11.09.2026 11:45 — «ПАО «Группа Позитив» (Positive
  Technologies) закрыло сделку по приобретению 33% акций компании CyberOK»;
- Sostav, 11.09.2026 13:00 — 33%, юрлица обеих сторон, «Об этом сообщается в
  материалах, размещенных в центре раскрытия корпоративной информации»
  (первоисточник — раскрытие ПАО «Группа Позитив»; e-disclosure.ru из этой
  среды роботам не отвечает, 403 — читалось через перепечатки);
- CNews, 11.09.2026 13:38 — полный текст пресс-релиза Positive Technologies;
- Anti-Malware, 11.09.2026 11:49 — то же, независимой редакцией.

Финансы АО «Сайбер ОК» (ГИР БО 2025) и ИНН вносятся не здесь, а
`pipeline/fix_pt_cyberok_legal_entities_and_financials.py`: это данные
реестра, а не цитата.

Запуск: python3 pipeline/ingest/review.py [--write]
"""

TELESPUTNIK = 'https://telesputnik.ru/materials/companies/news/positive-technologies-kupila-33-akcii-ib-kompanii-cyberok'
SOSTAV = 'https://www.sostav.ru/publication/positive-technologies-priobrela-33-razrabotchika-reshenij-dlya-kiberbezopasnosti-cyberok-86868.html'
CNEWS = 'https://www.cnews.ru/news/line/2026-09-11_positive_technologies_priobrela_dolyu'
ANTIMALWARE = 'https://www.anti-malware.ru/news/2026-09-11-111332/51380'

QUOTE_SHARE = (
    'ПАО «Группа Позитив» (Positive Technologies) закрыло сделку по '
    'приобретению 33% акций компании CyberOK.'
)
QUOTE_SOSTAV = (
    'ИБ-компания Positive Technologies (юрлицо — ПАО «Группа Позитив») '
    'приобрела 33% разработчика решений в области кибербезопасности CyberOK '
    '(АО «Сайбер ОК»). Об этом сообщается в материалах, размещенных в центре '
    'раскрытия корпоративной информации. Сумма сделки не раскрывается.'
)
QUOTE_CNEWS = (
    'Positive Technologies объявила о приобретении доли в компании-разработчике '
    'решений в области кибербезопасности CyberOK.'
)
QUOTE_AM = (
    'Positive Technologies приобрела долю в разработчике решений '
    'кибербезопасности CyberOK. Размер инвестиции и условия сделки компании '
    'не раскрыли.'
)

FIXES = [
    dict(id='gdc686ec2', field='eco.share',
         old='Доля в CyberOK. Размер доли стороны не назвали.',
         new='33% акций компании CyberOK',
         quote=QUOTE_SHARE,
         why='Telesputnik 11.09.2026: доля названа по раскрытию ПАО «Группа Позитив»'),
    dict(id='gdc686ec2', field='stake_acquired', old=None, new=33,
         quote=QUOTE_SHARE,
         why='Telesputnik 11.09.2026: «приобретению 33% акций компании CyberOK»'),
    dict(id='gdc686ec2', field='src', old=None, new=['Telesputnik', TELESPUTNIK],
         quote=QUOTE_SHARE, why='второй источник: доля 33%'),
    dict(id='gdc686ec2', field='src', old=None, new=['Sostav', SOSTAV],
         quote=QUOTE_SOSTAV, why='третий источник: юрлица сторон и ссылка на раскрытие'),
    dict(id='gdc686ec2', field='src', old=None, new=['CNews', CNEWS],
         quote=QUOTE_CNEWS, why='пресс-релиз Positive Technologies целиком'),
    dict(id='gdc686ec2', field='src', old=None, new=['Anti-Malware', ANTIMALWARE],
         quote=QUOTE_AM, why='независимое подтверждение, 11:49 МСК'),
]
