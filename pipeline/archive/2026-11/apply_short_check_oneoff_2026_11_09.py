# -*- coding: utf-8 -*-
"""Короткая проверка 9 ноября 2026 (партии sa–sj, 273 карточки с 3 октября): правки, которые review.py не умеет.

ЧТО ЧИНИТ. Десять помощников сверили каркас карточек, созданных с 3 октября 2026 (стороны,
дата и статус, сумма и доля, консультанты, заголовок по стандарту), со статьями и реестром
(pipeline/ingest/fixes/reread_2026_11_09_s{a..j}.py, тексты — data/inbox/triage/
sources_2026-11-09_s*.json). Кроме FIXES, в каждом файле лежит список ONE_OFF — то, что
таблица не берет: дата в другой месяц или год, только год или «unknown», даты этапов
events[], тип, статус без слова словаря, sum/eco.sum с sum_basis, retracted.*,
accepted_notes.*, party_evidence, law.adv (список), legal_short профилей. Поле `what` —
свободный текст; здесь он разобран в операции OPS (тег `sX[i]` — партия и номер в ONE_OFF).

Разбор `what`, где пришлось выбирать:
  * заголовки sc[0] g4b315d34, sd[0] g8cf4df95, sg[0] gf5bdb983, sf[5] gcb1ce023 — у поля уже
    есть запись FIXES другой партии; новое значение ставится здесь, прежняя запись
    получает отпечаток в proofread_absorbed (absorb_short_check_2026_11_09_chains.py).
  * снятая сумма (g4d7b2e19, g62577a1d) — в retracted.sum, sum_basis снимается вместе с суммой.
  * снятый продавец Сбербанк (g9fed3cb1), снятое описание вместо имени покупателя
    (g0158e326), неверное юрлицо покупателя (g3e6171f4, gc23d6f1a «Не раскрыт») —
    в retracted.<поле>, чтобы enrich.py не вернул их.
  * «date_basis» ставится там, где `why` называет основание (реестр — registry, день
    статьи — publication, заявление — announcement); у дат «только год» и «unknown»
    основание не ставится.
  * g90ccbac0 law.adv[0]: вместе с ролью «одной из сторон» переписана и заметка
    («сообщила, что сопровождала продавцов» — партия sf проверить этого не смогла: пост —
    картинка без текста), иначе роль и заметка противоречили бы друг другу.
  * gcb1ce023: стороны по реестру — источник datanewton (история участников) добавлен в src
    так же, как у ga09376f6; поле no_parties снимается (обе стороны найдены).
  * g5b2cf7bd: продавцы по Абирегу — адрес Абирега добавлен в src, если его там нет.
  * legal_short — здесь только те профили, где party_legal_names.py формы не выводит, теряет
    вложенные кавычки или пишет регистр реестра, а партия назвала форму явно
    (ППК «Фонд развития территорий», ПАО «МГТС», АО СЗ «Центр-Инвест», ООО «Ювелирный
    завод «ПАРС»», ПАО «Сахалинское морское пароходство», АО «ГМК «Дальполиметалл»»,
    АО «ГК «Мелком»» …). Остальные — `party_legal_names.py <id> --write` после этого скрипта.
    Не записано: покупатель gee625a0f (РМК) — реестр сопоставил его с ООО «Современные
    Управленческие Решения», это не то юрлицо, которое называет статья; продавец g6264541d
    («ГК Дело») — сопоставление отвергнуто в fns_registry.json; покупатель g25a6766d —
    партия его не сверяла.

Не взято отсюда ничего, что держится на нежелательных изданиях (UNDESIRABLE_HOSTS): в
ONE_OFF и FIXES их нет.

ЗАПУСК (после `MASS_OK=reread python3 pipeline/ingest/review.py --write`):
    python3 pipeline/archive/2026-11/apply_short_check_oneoff_2026_11_09.py            # сухой прогон
    MASS_OK=reread python3 pipeline/archive/2026-11/apply_short_check_oneoff_2026_11_09.py --write

Каждая операция проверяет старое значение (`assert`), база перечитывается прямо перед
записью, запись идет через `mass_edit_guard.check` (ключ пробы `reread`). Повторный запуск
после записи отказывает на первом же assert — это ожидаемо: скрипт разовый.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
sys.path.insert(0, ROOT)

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
MISSING = object()

DP_APPEAL = 'https://www.dp.ru/a/2025/12/12/apelljacija-podtverdila-perehod'
DP_LISITSA = 'https://www.dp.ru/a/2026/10/08/prava-trebovanija-k-zastrojshhiku'
UPT_REG = 'https://datanewton.ru/contragents/1025005598078/history/timeline'
ABIREG_UMBRELLA = 'https://abireg.ru/newsitem/119031-tsifrovye-privychki-priobretayut-razrabotchika-po-umbrella-it/'
CNEWS_EKSPANTA = ['CNews', 'https://www.cnews.ru/news/line/2026-11-06_ekspanta_voshla_v_kapital']
DESPORT_OLD = ('ООО «АРМ» продало здание бывшего гипермаркета Desport в Петербурге компании «Сити Капитал» за 458 '
               'млн рублей — единственная сделка на рынке торговой недвижимости города за девять месяцев 2026 года.')
DESPORT_NEW = ('ООО «АРМ» продало здание бывшего гипермаркета Desport в Петербурге компании «Сити Капитал»; по '
               'оценке аналитиков IBC Real Estate, за 458 млн рублей — единственная сделка на рынке торговой '
               'недвижимости города за девять месяцев 2026 года.')
NO_ADV = [['Стороны сделки', 'Не раскрывались', 'Юридические консультанты в публичных источниках не раскрывались']]

# fmt: off
OPS = [
 # ------------------------------------------------------------------ партия sa
 {'tag': 'sa[0]', 'op': 'set', 'id': 'gd937c845', 'field': 'date', 'old': '2026-09-28', 'new': '2026-11-03'},
 {'tag': 'sa[0]', 'op': 'set', 'id': 'gd937c845', 'field': 'date_basis', 'old': MISSING, 'new': 'announcement'},
 {'tag': 'sa[1]', 'op': 'set', 'id': 'g4d7b2e19', 'field': 'sum', 'old': '5–5,5 млрд ₽ (по оценке)', 'new': 'Не раскрыта'},
 {'tag': 'sa[1]', 'op': 'set', 'id': 'g4d7b2e19', 'field': 'eco.sum', 'old': '5–5,5 млрд ₽ (по оценке)', 'new': 'Не раскрыта'},
 {'tag': 'sa[1]', 'op': 'retract', 'id': 'g4d7b2e19', 'field': 'sum', 'new': ['5–5,5 млрд ₽ (по оценке)']},
 {'tag': 'sa[2]', 'op': 'set', 'id': 'gc93eac76', 'field': 'date', 'old': '2025-05-08', 'new': '2025-12-05'},
 {'tag': 'sa[2]', 'op': 'set', 'id': 'gc93eac76', 'field': 'date_basis', 'old': MISSING, 'new': 'registry'},
 {'tag': 'sa[2]', 'op': 'set', 'id': 'gc93eac76', 'field': 'party_evidence', 'old': MISSING,
  'new': {'target': [{'value': 'ООО «Руцис» (бывшее ООО «АББ»)', 'field': 'target', 'method': 'registry_owner_history',
                      'url': 'https://projectcompass.ru/api/companies/g7e2a8149/fns'}]}},
 {'tag': 'sa[3]', 'op': 'set', 'id': 'gd561d849', 'field': 'status', 'old': 'Обсуждается', 'new': 'Закрыта'},
 {'tag': 'sa[3]', 'op': 'src_add', 'id': 'gd561d849', 'new': ['Деловой Петербург', DP_APPEAL]},
 {'tag': 'sa[3]', 'op': 'replace', 'id': 'gd561d849', 'field': 'law.appr',
  'old': 'Итог обжалования в прочитанных статьях не найден.',
  'new': 'Тринадцатый арбитражный апелляционный суд оставил решение в силе (Деловой Петербург, 12 декабря 2025 года).'},
 {'tag': 'sa[4]', 'op': 'set', 'id': 'g4d7b2e19', 'field': 'eco.share',
  'old': 'АФК «Система» продала Альфа-Банку 4,85% акций «Медси» в рамках pre-IPO; у «Системы» остается 90,64%, еще '
         '4,5% принадлежат акционеру, которого компания не называет.',
  'new': '4,85% акций АО «Группа компаний «Медси»»; у АФК «Система» остается 90,64%, еще 4,5% — у акционера, '
         'которого «Система» не называет.'},
 {'tag': 'sa[5]', 'op': 'set', 'id': 'g08c11c6b', 'field': 'eco.share', 'old': '100% ООО «Ситрас»',
  'new': '100% доли в ООО «Ситрас» (ныне ООО «Акварель»)'},
 {'tag': 'sa[7]', 'op': 'legal', 'id': 'gba764f10', 'role': 'seller_id', 'new': 'ППК «Фонд развития территорий»'},

 # ------------------------------------------------------------------ партия sb
 {'tag': 'sb[0]', 'op': 'set', 'id': 'g9fed3cb1', 'field': 'seller', 'old': 'Сбербанк', 'new': 'ООО «СЗ «Северная Лисица»»'},
 {'tag': 'sb[0]', 'op': 'retract', 'id': 'g9fed3cb1', 'field': 'seller', 'new': ['Сбербанк']},
 {'tag': 'sb[1]', 'op': 'set', 'id': 'g9fed3cb1', 'field': 'seller_id', 'old': 'g28ff15bb', 'new': MISSING},
 {'tag': 'sb[2]', 'op': 'set', 'id': 'g9fed3cb1', 'field': 'party_evidence.seller',
  'old': [{'value': 'Сбербанк', 'field': 'seller', 'method': 'explicit_news_title', 'url': DP_LISITSA}],
  'new': [{'value': 'ООО «СЗ «Северная Лисица»»', 'field': 'seller', 'method': 'explicit_news_title', 'url': DP_LISITSA}]},
 {'tag': 'sb[3]', 'op': 'set_any', 'id': 'g9fed3cb1', 'field': 'party_evidence.target',
  'old': [[{'value': 'права требования к ООО «СЗ «Северная Лисица»', 'field': 'asset', 'method': 'explicit_news_title',
            'url': DP_LISITSA}],
          [{'value': 'жилой комплекс премиум-класса «Резиденции Присутствия» на Приморском шоссе', 'field': 'asset',
            'method': 'human_review', 'url': DP_LISITSA}]],
  # review.py уже перевел свидетельство на новое значение asset (method human_review) — так и остается.
  'new': [{'value': 'жилой комплекс премиум-класса «Резиденции Присутствия» на Приморском шоссе', 'field': 'asset',
           'method': 'human_review', 'url': DP_LISITSA}]},
 {'tag': 'sb[0]', 'op': 'note', 'id': 'g9fed3cb1', 'path': 'no_profile.seller',
  'new': 'продавец — застройщик ООО «СЗ «Северная Лисица»» (по исправленной статье «Делового Петербурга»), '
         'профиль компании не заводился; Сбербанк в статье — только кредитор стройки'},
 {'tag': 'sb[0]', 'op': 'append_note', 'id': 'g9fed3cb1', 'path': 'notes',
  'new': ' Короткая проверка 9 ноября 2026: «Деловой Петербург» исправил статью — ЖК одним лотом за 1,318 млрд ₽ '
         'продает сам застройщик ООО «СЗ «Северная Лисица»», а Сбербанк — кредитор стройки (кредитная линия на '
         '370 млн ₽); написанное выше о правах требования Сбербанка устарело.'},
 {'tag': 'sb[4]', 'op': 'set', 'id': 'g62577a1d', 'field': 'sum', 'old': '2 млрд ₽', 'new': 'Не раскрыта'},
 {'tag': 'sb[5]', 'op': 'set', 'id': 'g62577a1d', 'field': 'eco.sum', 'old': '2 млрд ₽', 'new': 'Не раскрыта'},
 {'tag': 'sb[6]', 'op': 'set', 'id': 'g62577a1d', 'field': 'sum_basis', 'old': 'range', 'new': MISSING},
 {'tag': 'sb[4]', 'op': 'retract', 'id': 'g62577a1d', 'field': 'sum', 'new': ['2 млрд ₽']},
 {'tag': 'sb[7]', 'op': 'set', 'id': 'g0710e7a1', 'field': 'date', 'old': '2026-10-06', 'new': '2026-10-05'},
 {'tag': 'sb[8]', 'op': 'set', 'id': 'g0710e7a1', 'field': 'date_basis', 'old': MISSING, 'new': 'publication'},
 {'tag': 'sb[9]', 'op': 'set', 'id': 'gc7143483', 'field': 'law.adv', 'old': [],
  'new': [['Юридический консультант продавца (Frigoglass)', 'Milbank',
           'Регуляторные вопросы США и ЕС, в том числе санкции; партнеры Биджан Ганджи и Андреа Гамильтон '
           '(по данным сайта фирмы)']]},
 {'tag': 'sb[10]', 'op': 'set', 'id': 'g86cc01b0', 'field': 'law.adv', 'old': NO_ADV, 'new': []},
 {'tag': 'sb[11]', 'op': 'set', 'id': 'gb6d97747', 'field': 'law.adv', 'old': NO_ADV, 'new': []},

 # ------------------------------------------------------------------ партия sc
 {'tag': 'sc[0]', 'op': 'set', 'id': 'g4b315d34', 'field': 'title',
  'old': 'Группа «Эфко» решила продать бизнес-центр «Аркус IV» в Москве',
  'new': 'Бизнес-центр «Аркус IV» группы «Эфко» выставлен на продажу'},
 {'tag': 'sc[1]', 'op': 'event', 'id': 'g19410fc2', 'index': 0, 'old': {'kind': 'closed', 'date': '2026-10-16'},
  'new': {'date': '2026-10-15'}},
 {'tag': 'sc[2]', 'op': 'event', 'id': 'gfc3e1ae2', 'index': 0, 'old': {'kind': 'closed', 'date': '2026-10-16'},
  'new': {'date': '2026-10-15'}},
 {'tag': 'sc[3]', 'op': 'set', 'id': 'gaa5d4eb6', 'field': 'date', 'old': '2026-09-01', 'new': '2026'},
 {'tag': 'sc[4]', 'op': 'set', 'id': 'g00f36bab', 'field': 'date', 'old': '2026-11-09', 'new': '2026'},
 {'tag': 'sc[5]', 'op': 'set', 'id': 'g3e6171f4', 'field': 'date', 'old': '2022-05-16', 'new': '2022-05-20'},
 {'tag': 'sc[5]', 'op': 'set', 'id': 'g3e6171f4', 'field': 'date_basis', 'old': MISSING, 'new': 'registry'},
 {'tag': 'sc[6]', 'op': 'set', 'id': 'g3e6171f4', 'field': 'buyer_name',
  'old': 'Местное руководство заводов (ООО «Ново Пакаджинг ББ»)', 'new': 'Местное руководство заводов (ООО «Новопак»)'},
 {'tag': 'sc[6]', 'op': 'retract', 'id': 'g3e6171f4', 'field': 'buyer_name',
  'new': ['Местное руководство заводов (ООО «Ново Пакаджинг ББ»)']},
 {'tag': 'sc[6]', 'op': 'set', 'id': 'g3e6171f4', 'field': 'party_evidence', 'old': MISSING,
  'new': {'buyer': [{'value': 'Местное руководство заводов (ООО «Новопак»)', 'field': 'buyer_name',
                     'method': 'registry_owner_history',
                     'url': 'https://projectcompass.ru/api/companies/gfc9da58b/fns'}]}},
 {'tag': 'sc[7]', 'op': 'set', 'id': 'gb92f7119', 'field': 'eco.share',
  'old': '100% долей ООО «Селаникар» (юрлицо Carprice), оформленных на кипрскую Vendebita Trading Ltd.',
  'new': '100% долей ООО «Селаникар» (юрлицо Carprice).'},

 # ------------------------------------------------------------------ партия sd
 {'tag': 'sd[0]', 'op': 'set', 'id': 'g8cf4df95', 'field': 'title',
  'old': '«Сибпромстрой» выставил на продажу офисно-торговое здание в Сургуте за 614,5 млн рублей',
  'new': 'Торгово-офисное здание «Сибпромстроя» в Сургуте выставлено на продажу за 614,5 млн рублей'},
 {'tag': 'sd[1]', 'op': 'set', 'id': 'gf6c084b9', 'field': 'eco.finadv', 'old': '—',
  'new': 'Advance Capital — финансовый консультант продавцов (основатели Swordfish Security Александр Пинаев и '
         'Юрий Сергеев)'},
 {'tag': 'sd[2]', 'op': 'set', 'id': 'gf6c084b9', 'field': 'law.adv',
  'old': [['Консультант продавца', 'ALUMNI Partners',
           '«Команда ALUMNI Partners консультировала основателей ГК Swordfish Security в знаковой сделке для '
           'российского рынка» кибербезопасности; руководитель — партнер Антон Панченков. Источник: '
           't.me/alumnipartnerslawfirm/2844'],
          ['Консультант покупателя', 'BIRCH',
           'Корпоративная / M&A практика BIRCH консультировала покупателя — ЗПИФ под управлением АО «ВИМ '
           'Инвестиции». Источник: t.me/BIRCHLEGAL/2343']],
  'new': [['Юридический консультант продавцов (основатели Swordfish Security Александр Пинаев и Юрий Сергеев)',
           'ALUMNI Partners',
           '«Команда ALUMNI Partners консультировала основателей ГК Swordfish Security в знаковой сделке для '
           'российского рынка» кибербезопасности; руководитель — партнер Антон Панченков. Источник: '
           't.me/alumnipartnerslawfirm/2844'],
          ['Юридический консультант покупателя (ЗПИФ «Пре-АйПиО 2» под управлением «ВИМ Инвестиций»)', 'BIRCH',
           'Корпоративная / M&A практика BIRCH консультировала покупателя — ЗПИФ под управлением АО «ВИМ '
           'Инвестиции». Источник: t.me/BIRCHLEGAL/2343']]},
 {'tag': 'sd[3]', 'op': 'evidence', 'id': 'gf6c084b9', 'role': 'seller',
  'new': [{'value': 'Александр Пинаев и Юрий Сергеев', 'field': 'seller', 'method': 'human_review',
           'url': 'https://t.me/rusven/7802'}]},
 {'tag': 'sd[4]', 'op': 'evidence_value', 'id': 'gee625a0f', 'role': 'target',
  'old': ['100% ООО «Красная руда» (8 лицензий на геологическое изучение недр на Алтае)', '100% ООО «Красная руда»'],
  'new': '100% ООО «Красная руда»'},

 # ------------------------------------------------------------------ партия se (только legal_short)
 {'tag': 'se[0]', 'op': 'legal', 'id': 'gae005e6f', 'role': 'buyer', 'new': 'ПАО «МГТС»'},
 {'tag': 'se[1]', 'op': 'legal', 'id': 'ge9d4edaa', 'role': 'buyer', 'new': 'АО «ГК «Мелком»»'},
 {'tag': 'se[1]', 'op': 'legal', 'id': 'ge9d4edaa', 'role': 'target', 'new': 'ООО «Русский лен»'},
 {'tag': 'se[2]', 'op': 'legal', 'id': 'g38bdff94', 'role': 'buyer', 'new': 'ООО «Гидромаш МСК»'},
 {'tag': 'se[2]', 'op': 'legal', 'id': 'g38bdff94', 'role': 'target', 'new': 'ООО «Гидроиндустрия»'},

 # ------------------------------------------------------------------ партия sf
 {'tag': 'sf[0]', 'op': 'set', 'id': 'gcb1ce023', 'field': 'seller', 'old': MISSING, 'new': 'Александр Казаков'},
 {'tag': 'sf[1]', 'op': 'set', 'id': 'gcb1ce023', 'field': 'buyer_name', 'old': MISSING, 'new': 'АО «Тау Капитал»'},
 {'tag': 'sf[0]', 'op': 'set', 'id': 'gcb1ce023', 'field': 'party_evidence', 'old': MISSING,
  'new': {'seller': [{'value': 'Александр Казаков', 'field': 'seller', 'method': 'registry', 'url': UPT_REG}],
          'buyer': [{'value': 'АО «Тау Капитал»', 'field': 'buyer_name', 'method': 'registry', 'url': UPT_REG}]}},
 {'tag': 'sf[0]', 'op': 'src_add', 'id': 'gcb1ce023',
  'new': ['ЕГРЮЛ: история участников ООО «Универсальные пищевые технологии»', UPT_REG]},
 {'tag': 'sf[2]', 'op': 'set', 'id': 'gcb1ce023', 'field': 'no_parties',
  'old': 'Продавец («акционер») и покупатель («частный инвестор») не названы', 'new': MISSING},
 {'tag': 'sf[3]', 'op': 'set', 'id': 'gcb1ce023', 'field': 'date', 'old': '2024', 'new': '2024-08-28'},
 {'tag': 'sf[3]', 'op': 'set', 'id': 'gcb1ce023', 'field': 'date_basis', 'old': MISSING, 'new': 'registry'},
 {'tag': 'sf[4]', 'op': 'set', 'id': 'gcb1ce023', 'field': 'eco.share',
  'old': 'Бизнес производителя чая «Универсальные пищевые технологии».',
  'new': '73,55% доли в ООО «Универсальные пищевые технологии»'},
 {'tag': 'sf[5]', 'op': 'set', 'id': 'gcb1ce023', 'field': 'title',
  'old': 'Акционер продал производителя чая «Универсальные пищевые технологии» частному инвестору',
  'new': 'АО «Тау Капитал» купило 73,55% производителя чая «Универсальные пищевые технологии»'},
 {'tag': 'sf[6]', 'op': 'set', 'id': 'g90ccbac0', 'field': 'law.adv.0',
  'old': ['Инвестиционный консультант', 'Atomic Capital',
          'Atomic Capital в своем Telegram-канале сообщила, что сопровождала продавцов; Mergers.ru называет ее '
          'инвестиционным консультантом сделки'],
  'new': ['Инвестиционный консультант одной из сторон', 'Atomic Capital',
          'Mergers.ru называет Atomic Capital инвестиционным консультантом сделки; чью сторону она представляла, '
          'источники не уточняют']},
 {'tag': 'sf[7]', 'op': 'set', 'id': 'g0158e326', 'field': 'buyer_name',
  'old': 'Крупная инвестиционная компания (название не раскрыто)', 'new': MISSING},
 {'tag': 'sf[7]', 'op': 'retract', 'id': 'g0158e326', 'field': 'buyer_name',
  'new': ['Крупная инвестиционная компания (название не раскрыто)']},
 {'tag': 'sf[7]', 'op': 'set', 'id': 'g0158e326', 'field': 'party_evidence.buyer',
  'old': [{'value': 'Крупная инвестиционная компания (название не раскрыто)', 'field': 'buyer_name',
           'method': 'explicit_news_title',
           'url': 'https://www.vedomosti.ru/finance/articles/2026/10/15/1237169-mgkl-nashla-investora'}],
  'new': MISSING},
 {'tag': 'sf[8]', 'op': 'set', 'id': 'gdf5fb4fe', 'field': 'eco.share',
  'old': '100% уставного капитала ООО «Ниссан Мэнуфэкчуринг Рус» (завод в Санкт-Петербурге).',
  'new': '100% доли в ООО «Ниссан Мэнуфэкчуринг Рус»'},
 {'tag': 'sf[11]', 'op': 'legal', 'id': 'g6264541d', 'role': 'target', 'new': 'ПАО «Сахалинское морское пароходство»'},
 {'tag': 'sf[15]', 'op': 'legal', 'id': 'gadee3ca7', 'role': 'seller_id', 'new': 'ООО «Ава Дом»'},
 {'tag': 'sf[15]', 'op': 'legal', 'id': 'gadee3ca7', 'role': 'target', 'new': 'ООО «Ривьера Парк»'},

 # ------------------------------------------------------------------ партия sg
 {'tag': 'sg[0]', 'op': 'set', 'id': 'gf5bdb983', 'field': 'title',
  'old': '«Стройдевелопмент» выкупил застройщика недостроенного бизнес-центра на Гвардейской площади в Ростове',
  'new': '«Стройдевелопмент» купил застройщика недостроенного делового центра на Гвардейской площади в Ростове'},
 {'tag': 'sg[1]', 'op': 'set', 'id': 'g221460e5', 'field': 'eco.sum', 'old': '395 млн ₽', 'new': '395 млн ₽ (по оценке)'},
 {'tag': 'sg[2]', 'op': 'set', 'id': 'g22d3599c', 'field': 'sum', 'old': '155,4 млн ₽', 'new': '155,4 млн ₽ (стартовая цена)'},
 {'tag': 'sg[3]', 'op': 'set', 'id': 'g22d3599c', 'field': 'eco.sum', 'old': '155,4 млн ₽', 'new': '155,4 млн ₽ (стартовая цена)'},
 {'tag': 'sg[4]', 'op': 'set', 'id': 'geddb685d', 'field': 'sum', 'old': '1 ₽', 'new': '1 ₽ (стартовая цена)'},
 {'tag': 'sg[5]', 'op': 'set', 'id': 'geddb685d', 'field': 'eco.sum', 'old': '1 ₽', 'new': '1 ₽ (стартовая цена)'},
 {'tag': 'sg[6]', 'op': 'legal', 'id': 'gcd8d2664', 'role': 'seller_id', 'new': 'АО СЗ «Центр-Инвест»'},
 {'tag': 'sg[11]', 'op': 'set', 'id': 'g11e381eb', 'field': 'law.adv', 'old': NO_ADV,
  'new': [['Юридический консультант продавца (Huhtamaki)', 'Castrén & Snellman',
           'Сопровождение продажи российского бизнеса Huhtamaki компании Espetina Ltd. '
           'Источник: castren.fi/cases/huhtamaki-sale-of-russian-operations/']]},

 # ------------------------------------------------------------------ партия sh
 {'tag': 'sh[0]', 'op': 'set', 'id': 'g01993028', 'field': 'date', 'old': '2026-08-15', 'new': '2026'},
 {'tag': 'sh[1]', 'op': 'event', 'id': 'g01993028', 'index': 0, 'old': {'kind': 'closed', 'date': '2026-08-15'},
  'new': {'date': '2026'}},
 {'tag': 'sh[4]', 'op': 'src_remove', 'id': 'ga09376f6', 'old': CNEWS_EKSPANTA},
 {'tag': 'sh[5]', 'op': 'event_src_remove', 'id': 'ga09376f6', 'index': 0, 'old': CNEWS_EKSPANTA},
 {'tag': 'sh[6]', 'op': 'legal', 'id': 'ga09376f6', 'role': 'target', 'new': 'ООО «СиЭс Технологии»'},
 {'tag': 'sh[7]', 'op': 'set', 'id': 'ge881187c', 'field': 'date', 'old': '2026-06-30', 'new': '2026'},
 {'tag': 'sh[8]', 'op': 'event', 'id': 'ge881187c', 'index': 0, 'old': {'kind': 'closed', 'date': '2026-10-22'},
  'new': {'date': '2026'}},
 {'tag': 'sh[9]', 'op': 'replace', 'id': 'ge881187c', 'field': 'eco.context',
  'old': 'точный день сделки ни один источник не называет, поэтому в карточке стоит конец полугодия как крайний срок, '
         'когда она уже отражена в отчетности.',
  'new': 'точный день сделки ни один источник не называет.'},
 {'tag': 'sh[10]', 'op': 'legal', 'id': 'g25a6766d', 'role': 'target', 'new': 'ООО «Бэггинс кофе»'},
 {'tag': 'sh[11]', 'op': 'set', 'id': 'g25a6766d', 'field': 'eco.share',
  'old': 'Фонд «Бумеранг Капитал» выкупил 50% Baggins Coffee и стал управляющим партнером. Остальные 50% получил '
         'предприниматель Антон Петров, сооснователь «Цех 85».',
  'new': '100% доли в ООО «Бэггинс кофе»: по 50% у фонда «Бумеранг Капитал» (управляющий партнер) и у Антона '
         'Петрова, сооснователя «Цех 85».'},
 {'tag': 'sh[12]', 'op': 'set', 'id': 'g4f9a1741', 'field': 'eco.share',
  'old': 'По неофициальным данным, в иске названы 50% уставного капитала ООО «Инфорион».',
  'new': '100% доли в ООО «Инфорион».'},
 {'tag': 'sh[13]', 'op': 'set', 'id': 'g06adc4cc', 'field': 'status', 'old': 'Обсуждается', 'new': 'Закрыта'},
 {'tag': 'sh[14]', 'op': 'set', 'id': 'gad9394d1', 'field': 'status', 'old': 'Обсуждается', 'new': 'Закрыта'},
 {'tag': 'sh[15]', 'op': 'set', 'id': 'gaf4a976a', 'field': 'date', 'old': '2023-04-05', 'new': '2023'},
 {'tag': 'sh[16]', 'op': 'set', 'id': 'g13f5c85b', 'field': 'law.adv.0.0', 'old': 'Консультант сделки',
  'new': 'Консультант одной из сторон'},
 {'tag': 'sh[17]', 'op': 'set', 'id': 'g41bcec82', 'field': 'eco.share',
  'old': 'Вместе с компанией продается земля под рынком — 1,1963 га; на участке есть публичный сервитут под '
         'высоковольтную линию и семь зданий без обременения.',
  'new': '100% доли в ООО «Центральный городской рынок».'},
 {'tag': 'sh[18]', 'op': 'set', 'id': 'g41bcec82', 'field': 'eco.context', 'old': '—',
  'new': 'Вместе с компанией продается земля под рынком — 1,1963 га; на участке есть публичный сервитут под '
         'высоковольтную линию и семь зданий без обременения.'},

 # ------------------------------------------------------------------ партия si
 {'tag': 'si[0]', 'op': 'set', 'id': 'g6c2af36f', 'field': 'eco.sum', 'old': '224,8 тыс. евро (≈20,3 млн ₽)',
  'new': '€224,8 тыс. (≈20,3 млн ₽)'},
 {'tag': 'si[1]', 'op': 'set', 'id': 'g5b2cf7bd', 'field': 'seller', 'old': MISSING,
  'new': 'Станислав Мешков и Михаил Меньшинский'},
 {'tag': 'si[1]', 'op': 'evidence', 'id': 'g5b2cf7bd', 'role': 'seller',
  'new': [{'value': 'Станислав Мешков и Михаил Меньшинский', 'field': 'seller', 'method': 'article_text',
           'url': ABIREG_UMBRELLA,
           'quote': 'Продавцами выступили Станислав Мешков и генеральный директор Umbrella IT Михаил Меньшинский .'}]},
 {'tag': 'si[1]', 'op': 'src_add', 'id': 'g5b2cf7bd', 'new': ['Абирег', ABIREG_UMBRELLA]},
 {'tag': 'si[1]', 'op': 'note_replace', 'id': 'g5b2cf7bd', 'path': 'no_profile.seller',
  'new': 'два физлица, профиль не заводится; продавцы — по Абирегу и реестру'},
 {'tag': 'si[3]', 'op': 'legal', 'id': 'gbe13372d', 'role': 'buyer', 'new': 'АО «РПК»'},
 {'tag': 'si[3]', 'op': 'legal', 'id': 'gbe13372d', 'role': 'target', 'new': 'АО «ГМК «Дальполиметалл»»'},
 {'tag': 'si[4]', 'op': 'set', 'id': 'gbe13372d', 'field': 'law.struct',
  'old': 'Торги прошли без конкуренции: РПК была единственным претендентом и предложила 553,74 млн ₽ — выше '
         'стартовой цены лота, 535,743 млн ₽. Государству принадлежит 67% акций «Дальполиметалла», а '
         'перерегистрация оставшихся 33% пока не завершена.',
  'new': 'Торги прошли без конкуренции: РПК была единственным участником и предложила 553,74 млн ₽ — по данным '
         '«Коммерсанта», это начальная цена. В объявлении о торгах, которое пересказал MarketPower, начальная '
         'цена — 535,743 млн ₽. Государству принадлежит 67% акций «Дальполиметалла», а перерегистрация '
         'оставшихся 33% пока не завершена.'},
 {'tag': 'si[6]', 'op': 'set', 'id': 'ged24607a', 'field': 'law.adv',
  'old': [['Продавец и покупатель', 'NF Group', 'Консультант назван в Ведомостях; чью сторону представлял, статья не уточняет']],
  'new': [['Консультант одной из сторон', 'NF Group',
           'Консультантом сделки назван в Ведомостях; чью сторону представлял, ни статья, ни сообщения NF Group не уточняют']]},

 # ------------------------------------------------------------------ партия sj
 {'tag': 'sj[0]', 'op': 'set', 'id': 'g53da1f4d', 'field': 'type', 'old': 'M&A', 'new': 'Инвестиция'},
 {'tag': 'sj[1]', 'op': 'set', 'id': 'g53da1f4d', 'field': 'date', 'old': '2026-10-05', 'new': '2026-04-17'},
 {'tag': 'sj[1]', 'op': 'set', 'id': 'g53da1f4d', 'field': 'date_basis', 'old': MISSING, 'new': 'registry'},
 {'tag': 'sj[2]', 'op': 'event', 'id': 'g53da1f4d', 'index': 0, 'old': {'kind': 'closed', 'date': '2026-10-05'},
  'new': {'date': '2026-04-17'}},
 {'tag': 'sj[4]', 'op': 'set', 'id': 'g83ad1f72', 'field': 'date', 'old': '2026-10-13', 'new': '2026-10-05'},
 {'tag': 'sj[4]', 'op': 'set', 'id': 'g83ad1f72', 'field': 'date_basis', 'old': MISSING, 'new': 'registry'},
 {'tag': 'sj[5]', 'op': 'event', 'id': 'g83ad1f72', 'index': 0, 'old': {'kind': 'closed', 'date': '2026-10-13'},
  'new': {'date': '2026-10-05'}},
 {'tag': 'sj[7]', 'op': 'event', 'id': 'gd09e0945', 'index': 3, 'old': {'kind': 'closed', 'date': '2026-10-16'},
  'new': {'date': '2026-10-15'}},
 {'tag': 'sj[10]', 'op': 'legal', 'id': 'gf31c1d53', 'role': 'seller_id', 'new': 'ООО «Ювелирный завод «ПАРС»»'},
 {'tag': 'sj[11]', 'op': 'set', 'id': 'g4a53d81b', 'field': 'date', 'old': '2026-10-26', 'new': '2026'},
 {'tag': 'sj[12]', 'op': 'event', 'id': 'g4a53d81b', 'index': 0,
  'old': {'kind': 'closed', 'date': '2026-10-26', 'note': DESPORT_OLD}, 'new': {'date': '2026', 'note': DESPORT_NEW}},
 {'tag': 'sj[13]', 'op': 'set', 'id': 'g1eda1117', 'field': 'date', 'old': '2026-11-05', 'new': 'unknown'},
 {'tag': 'sj[14]', 'op': 'event', 'id': 'g1eda1117', 'index': 0, 'old': {'kind': 'closed', 'date': '2026-11-05'},
  'new': {'date': 'unknown'}},
 {'tag': 'sj[15]', 'op': 'set', 'id': 'g2ab91f78', 'field': 'law.adv',
  'old': [['Юридический консультант', 'Buzko Legal', 'консультант «Концентрации»: партнер Ирина Карева, юрист Анастасия Максимова']],
  'new': [['Юридический консультант компании («Концентрация»)', 'Buzko Legal',
           'Партнер Ирина Карева, юрист Анастасия Максимова (по данным Telegram-канала фирмы)']]},
 {'tag': 'sj[16]', 'op': 'set', 'id': 'gd1dabb38', 'field': 'law.adv', 'old': NO_ADV, 'new': []},
 {'tag': 'sj[17]', 'op': 'set', 'id': 'gc23d6f1a', 'field': 'law.adv', 'old': NO_ADV, 'new': []},
 {'tag': 'sj[18]', 'op': 'set', 'id': 'gc23d6f1a', 'field': 'buyer_name', 'old': 'Не раскрыт', 'new': MISSING},
]
# fmt: on


def _walk(obj, parts):
    for p in parts:
        if isinstance(obj, list):
            obj = obj[int(p)] if p.isdigit() and int(p) < len(obj) else MISSING
        elif isinstance(obj, dict):
            obj = obj.get(p, MISSING)
        else:
            return MISSING
    return obj


def _get(obj, field):
    return _walk(obj, field.split('.'))


def _set(obj, field, value):
    parts = field.split('.')
    for p in parts[:-1]:
        obj = obj[int(p)] if isinstance(obj, list) else obj.setdefault(p, {})
    last = parts[-1]
    if isinstance(obj, list):
        obj[int(last)] = value
    elif value is MISSING:
        obj.pop(last, None)
    else:
        obj[last] = value


def _apply(data, log):
    deals = {d['id']: d for d in data['deals']}
    comps = data['companies']
    for op in OPS:
        kind, tag = op['op'], op['tag']
        card = deals[op['id']]
        if kind == 'set':
            cur = _get(card, op['field'])
            assert cur == op['old'], (tag, op['id'], op['field'], cur)
            _set(card, op['field'], op['new'])
            log.append('%-7s %s %s' % (tag, op['id'], op['field']))
        elif kind == 'set_any':
            cur = _get(card, op['field'])
            assert cur in op['old'], (tag, op['id'], op['field'], cur)
            _set(card, op['field'], op['new'])
            log.append('%-7s %s %s' % (tag, op['id'], op['field']))
        elif kind == 'replace':
            cur = _get(card, op['field'])
            assert isinstance(cur, str) and cur.count(op['old']) == 1, (tag, op['id'], op['field'], cur)
            _set(card, op['field'], cur.replace(op['old'], op['new']))
            log.append('%-7s %s %s (фраза)' % (tag, op['id'], op['field']))
        elif kind == 'retract':
            lst = card.setdefault('retracted', {}).setdefault(op['field'], [])
            for v in op['new']:
                if v not in lst:
                    lst.append(v)
            log.append('%-7s %s retracted.%s' % (tag, op['id'], op['field']))
        elif kind == 'evidence':
            pe = card.setdefault('party_evidence', {})
            # review.py мог уже поставить свидетельство на то же значение (по адресу первой ссылки
            # карточки) — тогда оно заменяется свидетельством с адресом, который назвала партия.
            assert op['role'] not in pe or [e.get('value') for e in pe[op['role']]] == \
                [e['value'] for e in op['new']], (tag, op['id'], op['role'], pe.get(op['role']))
            pe[op['role']] = op['new']
            log.append('%-7s %s party_evidence.%s' % (tag, op['id'], op['role']))
        elif kind == 'evidence_value':
            ev = card['party_evidence'][op['role']][0]
            assert ev['value'] in op['old'], (tag, op['id'], ev)
            ev['value'] = op['new']
            log.append('%-7s %s party_evidence.%s[0].value' % (tag, op['id'], op['role']))
        elif kind == 'note':
            notes = card.setdefault('accepted_notes', {})
            assert _get(notes, op['path']) is MISSING, (tag, op['id'], op['path'])
            _set(notes, op['path'], op['new'])
            log.append('%-7s %s accepted_notes.%s' % (tag, op['id'], op['path']))
        elif kind == 'note_replace':
            notes = card['accepted_notes']
            assert isinstance(_get(notes, op['path']), str), (tag, op['id'], op['path'])
            _set(notes, op['path'], op['new'])
            log.append('%-7s %s accepted_notes.%s (заменена)' % (tag, op['id'], op['path']))
        elif kind == 'append_note':
            notes = card['accepted_notes']
            cur = notes[op['path']]
            assert op['new'].strip() not in cur, (tag, op['id'])
            notes[op['path']] = cur.rstrip() + op['new']
            log.append('%-7s %s accepted_notes.%s (дописано)' % (tag, op['id'], op['path']))
        elif kind == 'drop_note':
            notes = card['accepted_notes']
            assert notes.get(op['path']) == op['old'], (tag, op['id'], notes.get(op['path']))
            del notes[op['path']]
            if not notes:
                del card['accepted_notes']
            log.append('%-7s %s accepted_notes.%s снята' % (tag, op['id'], op['path']))
        elif kind == 'src_add':
            src = card.setdefault('src', [])
            if any(len(s) > 1 and s[1] == op['new'][1] for s in src):
                log.append('%-7s %s src уже есть %s' % (tag, op['id'], op['new'][1]))
            else:
                src.append(list(op['new']))
                log.append('%-7s %s src + %s' % (tag, op['id'], op['new'][1]))
        elif kind == 'src_remove':
            src = card.get('src') or []
            assert op['old'] in src, (tag, op['id'], src)
            src.remove(op['old'])
            assert any(len(s) > 1 and str(s[1]).startswith('http') for s in src), (tag, 'без http-ссылки')
            log.append('%-7s %s src − %s' % (tag, op['id'], op['old'][1]))
        elif kind == 'event_src_remove':
            ev = card['events'][op['index']]
            assert op['old'] in ev.get('sources', []), (tag, op['id'], ev.get('sources'))
            ev['sources'].remove(op['old'])
            assert ev.get('source') != op['old'], (tag, 'главный источник этапа — снимаемый')
            log.append('%-7s %s events[%d].sources − %s' % (tag, op['id'], op['index'], op['old'][1]))
        elif kind == 'event':
            ev = (card.get('events') or [None] * (op['index'] + 1))[op['index']]
            assert ev and all(ev.get(k) == v for k, v in op['old'].items()), (tag, op['id'], ev)
            ev.update(op['new'])
            log.append('%-7s %s events[%d] %s' % (tag, op['id'], op['index'], ', '.join(op['new'])))
        elif kind == 'legal':
            pid = card[op['role']]
            prof = comps[pid]
            assert prof.get('legal_short') in (None, op['new']), (tag, pid, prof.get('legal_short'))
            prof['legal_short'] = op['new']
            log.append('%-7s профиль %s (%s) legal_short = %s' % (tag, pid, prof.get('name'), op['new']))
        else:
            raise AssertionError('неизвестная операция %r' % kind)


def main(write=False):
    from pipeline import mass_edit_guard
    log = []
    data = json.load(open(DATA, encoding='utf-8'))
    _apply(data, log)
    print('\n'.join(log))
    print('Операций: %d, карточек: %d.' % (len(OPS), len({o['id'] for o in OPS})))
    if not write:
        print('Сухой прогон. Запись — с ключом --write (и MASS_OK=reread).')
        return
    fresh = json.load(open(DATA, encoding='utf-8'))     # перечитать прямо перед записью
    _apply(fresh, [])
    mass_edit_guard.check(json.load(open(DATA, encoding='utf-8')), fresh, os.environ.get('MASS_OK'))
    json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано. Дальше: absorb_short_check_2026_11_09_chains.py, party_legal_names.py --write, facts_derive.py --write.')


if __name__ == '__main__':
    main('--write' in sys.argv)
