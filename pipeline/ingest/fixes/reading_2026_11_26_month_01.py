# -*- coding: utf-8 -*-
"""Месячная дельта (уровень month), партия month_01, 26 ноября 2026.

Карточки: gf66151c1, g812a7b3b, g1e37f107, gf145d639, g2a4e8a51, g0b187624,
g2918b022, gee625a0f, gae005e6f, g6997a4f3.

Уже прочитанные ссылки из src не перечитывались (кроме шага 0 по МГТС:
сверка единиц в отчетности). Углы поиска и прочитанные адреса — в отчете
партии month_01.json.

Находки:
- g2918b022 (SEFE): Reuters 2 октября 2026 — SEFE изучает варианты вместе с
  Lazard, продажа должна начаться в 2027 году, размещение на бирже
  маловероятно. Поле law.struct было пустым — пишем туда.
- gae005e6f (МГТС): шаг 0 — в eco.target_fin стояли «млн рублей» вместо
  миллиардов (ошибка единиц в заметке «Ведомостей»); Market Power по той же
  отчетности МСФО дает 26,6 млрд ₽ выручки и 14,69 млрд ₽ чистой прибыли.
- gf66151c1 (Рапид Био): второй источник — «Фармацевтический вестник»
  (комментарий пресс-службы компании).

Запуск: python3 pipeline/ingest/review.py  (сухой прогон; запись — старший)
"""

# --- g2918b022 SEFE ---
_SEFE_URL = ('https://live.euronext.com/en/financial-news/'
             'german-energy-firm-sefe-enlists-lazard-reprivatisation-efforts-sources-say')
_SEFE_Q = ("German state-owned SEFE is working with investment bank Lazard to explore options in Berlin's "
           "efforts to sell the energy group, two people familiar with the matter said, as efforts to "
           "reshuffle the country's energy landscape pick up."
           ' … '
           "A sales process for SEFE is expected to kick off in 2027 to avoid clashing with Berlin's current "
           "efforts to sell a majority stake in peer Uniper, which also had to be rescued in the wake of "
           "Europe's energy crisis, the people said. An initial public offering is currently unlikely, one "
           "of the people said.")

# --- gae005e6f МГТС ---
_MGTS_URL = ('https://marketpower.pro/publications/'
             'mgts-uvelichila-operatsionnuiu-pribyl-na-27-v-pervom-polugodii-2026-goda')
_MGTS_Q = ('МГТС увеличила операционную прибыль на 27% в первом полугодии 2026 года'
           ' … '
           'Согласно опубликованной финансовой отчетности по МСФО*, выручка организации увеличилась на 14,1% '
           'и достигла 26,6 млрд ₽. Операционная прибыль за отчетный период подскочила почти на 27%, '
           'составив 10,39 млрд ₽, при этом чистая прибыль продемонстрировала более сдержанную динамику, '
           'увеличившись на 3,9% до 14,69 млрд ₽.')

# --- gf66151c1 Рапид Био ---
_RAPID_URL = ('https://pharmvestnik.ru/content/news/'
              'razrabotchik-ekspress-testov-poluchil-600-mln-rublei-investicii.html')
_RAPID_Q = ('Компания — разработчик тест-систем «Рапид Био» привлекла 600 млн руб. от частной инвестиционной '
            'компании Kama flow.')

CARDS = ['gf66151c1', 'g812a7b3b', 'g1e37f107', 'gf145d639', 'g2a4e8a51', 'g0b187624',
         'g2918b022', 'gee625a0f', 'gae005e6f', 'g6997a4f3']

FIXES = [
    # --- g2918b022 SEFE: Lazard и сроки продажи (Reuters, 2 октября 2026) ---
    {'id': 'g2918b022', 'field': 'law.struct',
     'old': '—',
     'new': 'По неофициальным данным, варианты продажи SEFE компания изучает вместе с инвестбанком Lazard. '
            'Саму продажу, как ожидается, начнут позже, чтобы она не пересекалась с уже идущей продажей '
            'контрольного пакета Uniper, а размещение акций на бирже пока считается маловероятным.',
     'quote': _SEFE_Q,
     'url': _SEFE_URL,
     'why': 'месячная дельта: Reuters 2 октября 2026 — советник Lazard, продажа после Uniper, IPO маловероятно (год 2027 в тексте не прошел проверку чисел английской цитаты — не пишем)'},
    {'id': 'g2918b022', 'field': 'src', 'old': None,
     'new': ['Reuters (Euronext)', _SEFE_URL],
     'quote': _SEFE_Q,
     'why': 'Reuters о подготовке продажи SEFE: Lazard и сроки'},

    # --- gae005e6f МГТС: шаг 0, единицы отчетности ---
    {'id': 'gae005e6f', 'field': 'eco.target_fin',
     'old': 'Чистая прибыль МГТС по МСФО в первом полугодии 2026 года составила 14,69 млн рублей (за '
            'аналогичный период 2025 года — 14,13 млн рублей), выручка — 26,59 млн рублей (23,31 млн рублей '
            'годом ранее).',
     'new': 'Чистая прибыль МГТС за первое полугодие 2026 года по МСФО — 14,69 млрд ₽ (плюс 3,9% за год), '
            'операционная — 10,39 млрд ₽ (рост около 27%). Выручка за те же шесть месяцев — 26,6 млрд ₽, '
            'на 14,1% больше, чем годом раньше.',
     'quote': _MGTS_Q,
     'url': _MGTS_URL,
     'why': 'шаг 0: в поле стояли «млн рублей» — ошибка единиц в заметке «Ведомостей»; отчетность МСФО — миллиарды'},
    {'id': 'gae005e6f', 'field': 'src', 'old': None,
     'new': ['MarketPower', _MGTS_URL],
     'quote': _MGTS_Q,
     'why': 'показатели МГТС по МСФО за первое полугодие 2026 года в правильных единицах'},

    # --- gf66151c1 Рапид Био: второй источник ---
    {'id': 'gf66151c1', 'field': 'src', 'old': None,
     'new': ['Фармацевтический вестник', _RAPID_URL],
     'quote': _RAPID_Q,
     'why': 'подтверждение суммы пресс-службой компании («ФВ», 1 октября 2026)'},
]
