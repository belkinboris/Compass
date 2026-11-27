# -*- coding: utf-8 -*-
"""Первый полный обыск (уровень day), партия day_13, 26 ноября 2026.

Карточки: g660f4097, gd77af086, g1e61ec63, g605d8d30, g5019c6ae.

Поиск источников:
  g660f4097 — сообщение Atria (уже в src): прибыль от продажи ~2 млн евро,
              курсовой убыток ~10 млн евро, бизнес был прибыльным — в eco.val.
              Шаг 0: в eco.context стоит переименование во «ВкусON» (сентябрь
              2022), источника в src не было — Sostav 30.09.2022. Retail.ru
              (пересказ «Ъ»: 1,5% продаж Atria против ~2% в сообщении Atria) —
              не записан, расходится с первоисточником.
  gd77af086 — Retail.ru (пересказ «Ъ», июль 2022: магазины перевесили вывески на
              «Хансен», чтобы договориться о поставках), Москвич Mag, Retail.ru
              ноябрь 2022 (Dan John). Нового сверх карточки — только ребрендинг
              июня 2022; абзац eco.context плотный (числа из «Ведомостей»), не
              дописан. Ничего не записано.
  g1e61ec63 — CRE (уже в src): слова Алексея Ефимова о цели — работать дальше
              независимой консалтинговой фирмой — в eco.rationale. Шаг 0:
              law.adv ссылается на New Retail, которого не было в src.
  g605d8d30 — пресс-релиз Wargaming 4 апреля 2022 (Cyprus Mail): компания не
              получит прибыли от передачи бизнеса и ждет значительных убытков —
              в eco.val. Шаг 0: eco.context говорит о передаче долей государству
              и продаже Росимуществом — в src этого не было: «Коммерсантъ»
              (октябрь 2026) и РАПСИ (решение суда 3 июня 2025).
  g5019c6ae — шаг 0: law.terms («Условия») держало расходы продавца на выход,
              это не условие сделки — перенесено в eco.val, law.terms снято.
              Юрлицо российской «дочки» снова не найдено (datanewton
              «Электролюкс» — 157 тезок, WebSearch «Электролюкс Профешнл»).

Запуск: python3 pipeline/ingest/review.py  (сухой прогон; запись — старший)
"""

_SB_ATRIA = 'https://www.inderes.fi/en/releases/atria-oyj-atria-sold-its-fast-food-business-in-russia'
_SB_SOSTAV = 'https://www.sostav.ru/publication/vkuson-56793.html'

_JLL_CRE = 'https://www.cre.ru/news/86916'
_JLL_NR = 'https://new-retail.ru/novosti/retail/jll_prodala_rossiyskiy_biznes_mestnomu_menedzhmentu9596/'

_LS_CYM = 'https://cyprus-mail.com/2022/04/04/wargaming-announces-decision-to-leave-russia-and-belarus'
_LS_KOM = 'https://www.kommersant.ru/doc/9027870'
_LS_RAPSI = 'https://rapsinews.ru/judicial_news/20250603/310923723.html'

_EP_IFX = 'https://interfax.com/newsroom/top-stories/81141/'
_EP_RETAIL = 'https://www.retail.ru/news/electrolux-prekrashchaet-deyatelnost-v-rossii-11-iyulya-2022-218467'

CARDS = ['g660f4097', 'gd77af086', 'g1e61ec63', 'g605d8d30', 'g5019c6ae']

FIXES = [
    # --- g660f4097 «Черкизово» / Atria / «Сибилла Рус» ---
    {'id': 'g660f4097', 'field': 'eco.val',
     'old': '—',
     'new': 'Atria сообщила, что бизнес был прибыльным; от продажи она ждала прибыли около 2 млн евро и, кроме того, курсового убытка около 10 млн евро, который не влияет на капитал и денежный поток группы.',
     'quote': 'The net sales of the fast food company operating in Russia has been approximately 2 percent of the Atria Group\'s total net sales and the business has been profitable. The fast food business is reported in the Atria Sweden segment. Atria will record a capital gain of approximately EUR 2 million from the divestment. In addition, a translation loss of approximately EUR 10 million is recorded from the transaction. The translation loss is recognized in EBIT, but it has no effect on the Group\'s equity nor cash flow.',
     'url': _SB_ATRIA,
     'why': 'сообщение продавца для биржи (уже в src): прибыль и курсовой убыток от продажи'},
    {'id': 'g660f4097', 'field': 'src', 'old': None,
     'new': ['Sostav', _SB_SOSTAV],
     'quote': '«Черкизово» приобрела бизнес быстрого питания «Сибилла Рус» в мае 2022 года у финской Atria. Сеть занимается продажей готовых решений для хот-догов, бургеров, тортилий и других блюд 16 лет. По условиям договора бренд Sibylla в сделку не вошёл, поэтому компания вынуждена переименовать проект.',
     'why': 'шаг 0: источник переименования во «ВкусON», которое уже стоит в eco.context'},

    # --- g1e61ec63 менеджмент / «Джонс Лэнг ЛаСаль» ---
    {'id': 'g1e61ec63', 'field': 'eco.rationale',
     'old': '—',
     'new': 'По словам нового гендиректора Алексея Ефимова, покупатели хотели и дальше работать в России как независимая консалтинговая фирма, сохранив ключевых специалистов и руководителей направлений.',
     'quote': 'Алексей Ефимов, генеральный директор ООО «Джонс Лэнг ЛаСаль» (после смены наименования – IBC Real Estate ), комментирует: «Мы рады объявить о завершении процесса по приобретению бизнеса у глобальной группы компаний JLL и продолжении работы в России в качестве независимой консалтинговой фирмы. Мы сохраняем всё лучшее, что нас выделяло на консалтинговом рынке, при этом продолжаем путь в отличной форме и оптимальном составе, более гибкие и эффективные. Мы сохранили ключевую экспертизу и лучших специалистов в сфере недвижимости, включая лидеров основных направлений бизнеса',
     'url': _JLL_CRE,
     'why': 'цель сделки словами покупателя (CRE, уже в src)'},
    {'id': 'g1e61ec63', 'field': 'src', 'old': None,
     'new': ['New Retail', _JLL_NR],
     'quote': 'Продавцом выступило Jones Lang LaSalle European Holdings Limited. Сделку сопровождали юридические компании Platforma.Legal и Alumni Partners.',
     'why': 'шаг 0: на этот адрес ссылается law.adv (Platforma.Legal), в src его не было'},

    # --- g605d8d30 Хатажаев / Wargaming / «Леста» ---
    {'id': 'g605d8d30', 'field': 'eco.val',
     'old': '—',
     'new': 'Wargaming заявила, что не получит от передачи бизнеса прибыли ни сейчас, ни в будущем, а напротив, ожидает значительных убытков.',
     'quote': 'Effective March 31, the company transferred its live games business in Russia and Belarus to the local management of Lesta Studio, which is no longer affiliated with Wargaming. The company will not profit from this process, neither today nor going forward; to the contrary, it expects to suffer substantial losses as a direct result of this decision.',
     'url': _LS_CYM,
     'why': 'пресс-релиз продавца 4 апреля 2022: цена не названа, но продавец заявил об убытках'},
    {'id': 'g605d8d30', 'field': 'src', 'old': None,
     'new': ['Cyprus Mail (пресс-релиз Wargaming)', _LS_CYM],
     'quote': 'The company will not profit from this process, neither today nor going forward; to the contrary, it expects to suffer substantial losses as a direct result of this decision.',
     'why': 'пресс-релиз продавца об уходе и передаче бизнеса «Лесте»'},
    {'id': 'g605d8d30', 'field': 'src', 'old': None,
     'new': ['Коммерсантъ', _LS_KOM],
     'quote': 'После начала СВО Wargaming объявила об уходе с российского рынка и выходе из капитала «Лесты». Компания перешла к Малику Хатажаеву, которого позднее признали одним из участников экстремистского и запрещенного в РФ объединения. Генпрокуратура наложила арест на активы «Лесты». Три компании разработчика, связанные с «Лестой», перешли в собственность Росимущества.',
     'why': 'шаг 0: источник последней фразы eco.context (переход к государству и продажа)'},
    {'id': 'g605d8d30', 'field': 'src', 'old': None,
     'new': ['РАПСИ', _LS_RAPSI],
     'quote': '«Суд, рассмотрев материалы дела, решил <…> обратить в доход государства 100% долей уставного капитала трех юрлиц «Леста игры», — сказал председательствующий судья Михаил Строгонов.',
     'why': 'шаг 0: источник решения суда 2025 года, упомянутого в eco.context'},

    # --- g5019c6ae Electrolux Professional / местный менеджмент ---
    {'id': 'g5019c6ae', 'field': 'law.terms',
     'old': 'Расходы на выход из России — 35 млн шведских крон, они отражены в отчетности за II квартал 2022 года как разовые.',
     'new': '—',
     'quote': 'This will incur a cost of SEK35 million that will be treated as items affecting comparability in the second quarter of 2022, the company said in a press release.',
     'url': _EP_IFX,
     'why': 'шаг 0: расходы продавца на выход — не условие сделки; перенесены в eco.val'},
    {'id': 'g5019c6ae', 'field': 'eco.val',
     'old': '—',
     'new': 'Цена не раскрыта. Выход из России обошелся Electrolux Professional в 35 млн шведских крон, их отразили как разовые расходы за II квартал 2022 года; другого заметного влияния на прибыль группы компания не ждала.',
     'quote': 'This will incur a cost of SEK35 million that will be treated as items affecting comparability in the second quarter of 2022, the company said in a press release. … Besides the exit cost of SEK35 million, the decision to leave Russia is not expected to have any material effect on the group\'s profit or profitability, the company said.',
     'url': _EP_IFX,
     'why': 'расходы продавца на выход и отсутствие иного влияния на прибыль (Интерфакс, уже в src)'},
    {'id': 'g5019c6ae', 'field': 'src', 'old': None,
     'new': ['Retail.ru', _EP_RETAIL],
     'quote': 'Решение повлечет за собой финансовые затраты в размере 35 миллионов шведских крон (3,3 миллиона долларов). В остальном передача российского бизнеса не будет иметь значительного влияния на прибыльность Electrolux. В России у Electrolux Professional 25 сотрудников.',
     'why': 'русскоязычный источник о расходах на выход и числе сотрудников'},
]
