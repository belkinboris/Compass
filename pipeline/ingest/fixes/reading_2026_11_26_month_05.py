# -*- coding: utf-8 -*-
"""Месячная дельта (уровень month), партия month_05, 26 ноября 2026.

Карточки: gfc3e1ae2, gf803c055, g38bdff94, g7bff6e5c, ga5a7f3c1, ga09376f6,
g28941fd8, g32cfa1d4, g7d3f5a20, gx4padel01.

Поиск (уже прочитанные ссылки src по существу не перечитывались; исключение —
t.me/rusven/7808 у ga09376f6: ее факты о цене в карточку не перенесены):
  gfc3e1ae2 (Ontex) — пресс-релиз Ontex 16 октября и отчет за третий квартал
              (28 октября): около 350 сотрудников, ~5% выручки и 7–8% EBITDA
              группы; деньги и аренда на конец сентября; исключение из
              отчетности в четвертом квартале -> eco.target_fin, eco.context, src.
  gf803c055 (Eviosys) — квартальный отчет Sonoco (10-Q): Россия — 1,1% продаж
              и 0,7% активов, Sonoco проверяет потерю контроля -> eco.context,
              eco.share (100% долей по указу, URA.RU), src. Дата карточки 16
              октября: Sonoco пишет «On October 16, 2026, the Russian government
              issued a decree», российские издания — указ от 15 октября; не правим.
  g38bdff94 (ГМС) — полная версия статьи «Коммерсанта» (doc/9027632): мнения
              Тихова («Аверта Групп») и Токаревой (Pen & Paper), обзор НКР о
              портфеле контрактов -> eco.rationale, eco.target_fin, src.
              AK&M и mergers.ru пересказывают «Коммерсант» — не взяты.
  g7bff6e5c (Visiology) — АБН 16 октября: итог полугодия с прибылью, клиенты
              -> extra, src. ComNews снова не отдает текст.
  ga5a7f3c1 (Aspace) — пост PRObonds 16 октября: место «Атолл Капитала» в
              совете директоров -> law.terms, src. mergers.ru, smart-lab — ничего.
  ga09376f6 («Стаксель») — ЕГРЮЛ 23 октября 2026: Скороход 100% -> 75%,
              «Экспанта» 25% (уставный капитал прежний) -> date, law.struct;
              @rusven (со ссылкой на Forbes): 50 млн ₽ за 25%, право докупить
              еще 25% за четыре года -> sum, eco.sum, eco.val, eco.share, eco.fin.
              Forbes закрыт капчей.
  g28941fd8 (VEON/Perfectum) — отчет VEON (6-K) и UzDaily: сделку закрыли
              27 октября; расчет деньгами и передачей здания -> status, date,
              title, eco.fin, eco.val, law.appr (снята фраза «планируют закрыть»), src.
  g32cfa1d4 (Salmon) — пресс-релиз (ANTARA/PRNewswire) и DealStreetAsia: $90 млн
              — обязательства инвесторов, 9 млн скачиваний -> law.struct,
              eco.target_fin, src.
  g7d3f5a20 (FESCO) — статус не сдвинулся (закрытия нет); Pravo.ru 18 августа:
              «Глобальную логистику» возглавила Екатерина Ляхова -> law.struct;
              Вгудок 18 ноября: оформление — до конца 2026 года -> extra, src.
  gx4padel01 (X4 Падел) — три угла, ничего сверх известного (новый клуб в
              Петербурге и лига — не про сделку).

Запуск: python3 pipeline/ingest/review.py  (сухой прогон; запись — старший)
"""

WHY = 'месячная дельта 26 ноября 2026 (партия month_05)'

ONTEX_Q3 = 'https://ontex.com/news/financial/transformation-of-ontex-progressing-well-q3-impacted-by-steep-input-cost-increases-full-year-adj-ebitda-outlook-lowered-to-e143-148-million/'
ONTEX_PR = 'https://www.sustainabilityhq.com/update-on-ontex-russia/'
VESTI = 'https://www.vesti.ru/ns/putin-peredal-vo-vremennoe-upravlenie-aktivy-kompanij-s-vyruchkoj-bolee-rub50-mlrd'
URA = 'https://ura.news/news/1053136498'
SONOCO = 'https://www.sec.gov/Archives/edgar/data/0000091767/000009176726000051/son-20260927.htm'
KOMM_GMS = 'https://www.kommersant.ru/doc/9027632'
ABN_VIS = 'https://abn.agency/2026/10/16/visiology-privlekla-200-mln-rublej/'
PROBONDS = 'https://t.me/probonds/17273'
DN_STAKSEL = 'https://datanewton.ru/api/v2/history?ogrn=1137746030982&startDate=2000-01-01&attributes=OWNERS'
RUSVEN_STAKSEL = 'https://t.me/rusven/7808'
CNEWS_STAKSEL = 'https://www.cnews.ru/news/line/2026-10-20_ekspanta_kupila_25_razrabotchika'
KOMM_STAKSEL = 'https://www.kommersant.ru/doc/9042127'
UZDAILY = 'https://www.uzdaily.uz/ru/beeline-uzbekistan-v-iiule-sentiabre-narastil-vyruchku-na-57/'
VEON_6K = 'https://www.sec.gov/Archives/edgar/data/0001468091/000146809126000046/veonltd6-kq326final.htm'
VEON_PR = 'https://www.veon.com/newsroom/press-releases/veon-accelerates-telecom-market-consolidation-in-uzbekistan-a-market-of-nearly-40-million-people'
SPOT_APPR = 'https://www.spot.uz/ru/2026/10/20/veon-perfectum-approval/'
ANTARA = 'https://en.antaranews.com/news/438315/salmon-secures-140-million-php-88-billion-to-double-down-on-the-growth-opportunity-in-the-philippines'
DSA = 'https://www.dealstreetasia.com/stories/philippines-fintech-salmon-secures-140m-in-additional-equity-debt-498489'
PRAVO_FESCO = 'https://pravo.ru/news/265342/'
LOGIRUS = 'https://logirus.ru/news/transport/led_tronulsya_dp_world_zashla_v_fesco_cherez_sever.html'
VGUDOK = 'https://vgudok.com/lenta/arabskiy-kapital-dlya-russkogo-severa-dva-medvedya-v-odnoy-berloge-zachem-rosatom-otdayot-49'

_ONTEX_Q3_QUOTE = ('Ontex Russia was placed under interim administration pursuant to a Russian presidential decree dated October 15, 2026. '
                   'A government-appointed interim administrator has assumed operational control of Ontex’s subsidiary, which will lead to its deconsolidation in the fourth quarter. '
                   'At the end of September, the Russian subsidiary held €19 million of cash and €30 million of lease liabilities. '
                   'As such, the deconsolidation reduces Ontex’s net financial debt by €10 million on a pro forma basis, '
                   'while the expected impact on the fourth-quarter adjusted EBITDA is a reduction by approximately €2 million.')

_ONTEX_PR_QUOTE = ('Ontex Russia currently employs around 350 employees and operates a production facility in Noginsk and sales office in Moscow. '
                   'Ontex Russia represents about 5% of the total revenue of Ontex Group, 7 to 8% of adj. EBITDA under IFRS consolidation rules and provides limited cash contribution.')

_SONOCO_QUOTE = ('On October 16, 2026, the Russian government issued a decree placing certain Russian assets associated with the Company’s metal packaging operations acquired as part of the Eviosys acquisition under temporary state administration. '
                 'The affected operations were acquired as part of the Company’s acquisition of Eviosys in December 2024 and are owned through a Dutch subsidiary of the Company. '
                 'The Company is evaluating the legal, operational and financial implications of the decree, including whether the action results in a loss of control over the affected operations. '
                 'As part of this assessment, the Company is evaluating whether the event may require the recognition of goodwill and other long-lived asset impairment charges, deconsolidation of the affected entities, or other related accounting impacts in future reporting periods. '
                 'The Company’s operations in Russia accounted for approximately 1.1% of consolidated net sales during the nine months ended September 27, 2026 and approximately 0.7% of total assets at September 27, 2026.')

_GMS_FIN_QUOTE = 'По последней раскрытой отчетности по МСФО, в 2024 году выручка группы ГМС увеличилась на 54%, до 95,5 млрд руб., EBITDA — на 47%, до 12,6 млрд руб., в том числе за счет реализации СПГ-проектов.'
_GMS_NKR_QUOTE = ('Агентство НКР в сентябрьском обзоре «Гидромашсервиса» обращало внимание, что на апрель 2026 года объем подписанных контрактов компании составлял 72 млрд руб., что на 27% меньше значения на апрель 2025 года. '
                  'Такое снижение в первую очередь объясняется завершением реализации крупнотоннажных проектов по сжижению природного газа с поставками в 2025–2026 годах, поясняли в НКР.')
_GMS_NKR2_QUOTE = 'Из-за сдвигов в сроках реализации крупных проектов восстановление выручки компании до значений 2024 года ожидается не ранее 2027 года, прогнозируют в НКР.'

_RUSVEN_PRICE = 'привлекла 50 млн рублей от холдинга промышленного ПО “Экспанта” в обмен на 25%.'
_RUSVEN_USE = ('Как пишет Forbes, половина привлеченных от “Экспанты” средств будет направлена на развитие существующего решения и запуск ИИ-агентов “Шкипер” '
               '- они будут помогать с поиском деталей, анализом процессов работы, проверкой документации и пр. Вторую часть денег получит Владимир Скороход. '
               'По условиям сделки “Экспанта” может купить еще 25% компании в течение четырех лет.')
_DN_2018 = '2018-05-25: было: СКОРОХОД ВЛАДИМИР ВИКТОРОВИЧ (ИНН: 780603484337) 50.0%; (5 000 руб.); стало: СКОРОХОД ВЛАДИМИР ВИКТОРОВИЧ (ИНН: 780603484337) 100.0%; (10 000 руб.)'
_DN_2026 = ('2026-10-23: было: СКОРОХОД ВЛАДИМИР ВИКТОРОВИЧ (ИНН: 780603484337) 100.0%; (10 000 руб.); стало: СКОРОХОД ВЛАДИМИР ВИКТОРОВИЧ (ИНН: 780603484337) 75.0%; (7 500 руб.) '
            '2026-10-23: было: —; стало: ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "ЭКСПАНТА" (ОГРН: 1217700020834) 25.0%; (2 500 руб.)')
_CNEWS_TRANCHES = 'Соглашение предполагает доведение доли до 50% в два транша. Средневзвешенная оценка по двум траншам составит 300 млн руб.'

_UZ_CLOSE = ('19 октября 2026 года VEON договорилась купить 100% Rubicon Wireless — мобильного оператора, который работает под брендом Perfectum. '
             'Сделку закрыли 27 октября, и с этой даты Perfectum входит в консолидированную отчетность VEON.')
_UZ_PRICE = ('Общая стоимость сделки — около $207 млн, включая примерно $93 млн финансового долга Perfectum, который переходит к покупателю. '
             'VEON рассчитывается с продавцом деньгами и передачей здания. Договор также предусматривает возмещение продавцу некоторых других расходов.')
_SPOT_APPR_QUOTE = ('В частности, Perfectum должен продолжать работу как самостоятельный оператор минимум 3 года после покупки. '
                    'Также ожидается расширение сети 5G Standalone в других регионах. '
                    'Компания должна сохранять текущие тарифы 5G FWA для действующих абонентов минимум 12 месяцев, обеспечить «комфортные условия» для новых пользователей и не снижать среднюю скорость интернета ниже уровня в 300 Мбит/с.')

CARDS = ['gfc3e1ae2', 'gf803c055', 'g38bdff94', 'g7bff6e5c', 'ga5a7f3c1',
         'ga09376f6', 'g28941fd8', 'g32cfa1d4', 'g7d3f5a20', 'gx4padel01']

FIXES = [
    # --- gfc3e1ae2 «Онтэкс РУ» ---
    {'id': 'gfc3e1ae2', 'field': 'src', 'old': None,
     'new': ['Ontex.com', ONTEX_Q3], 'quote': _ONTEX_Q3_QUOTE, 'url': ONTEX_Q3,
     'why': WHY + ': отчет Ontex за третий квартал — исключение из отчетности, деньги и аренда российской компании'},
    {'id': 'gfc3e1ae2', 'field': 'src', 'old': None,
     'new': ['Sustainabilityhq.com', ONTEX_PR], 'quote': _ONTEX_PR_QUOTE, 'url': ONTEX_PR,
     'why': WHY + ': пресс-релиз Ontex 16 октября (перепечатка GlobeNewswire) — штат и доля в выручке'},
    {'id': 'gfc3e1ae2', 'field': 'eco.target_fin',
     'old': 'Выручка компании — около 10,3 млрд руб. У российского подразделения Ontex — завод в Ногинске Московской области и офис продаж в Москве.',
     'new': 'Выручка компании — около 10,3 млрд руб. У российского подразделения Ontex — завод в Ногинске Московской области, офис продаж в Москве и около 350 сотрудников. '
            'Сама Ontex оценивает его вклад примерно в 5% выручки группы. '
            'На конец сентября 2026 года у российской компании было €19 млн денежных средств и €30 млн обязательств по аренде.',
     'quote': 'Выручка в 2025 году, согласно данным "СПАРК-Интерфакс", составила 10,3 млрд рублей. … ' + _ONTEX_PR_QUOTE + ' … ' + _ONTEX_Q3_QUOTE,
     'url': ONTEX_Q3, 'why': WHY + ': масштаб российской компании по данным самой Ontex'},
    {'id': 'gfc3e1ae2', 'field': 'eco.context',
     'old': 'Компания выпускает детские подгузники и женскую гигиеническую продукцию. Ее владелец — бельгийский производитель гигиенических товаров Ontex, работающий на разных рынках мира; один из его брендов — Helen Harper.',
     'new': 'Компания выпускает детские подгузники и женскую гигиеническую продукцию. Ее владелец — бельгийский производитель гигиенических товаров Ontex, работающий на разных рынках мира; один из его брендов — Helen Harper. '
            'После указа Ontex перестает учитывать российскую компанию в своей отчетности с четвертого квартала 2026 года; по расчету группы, ее скорректированная EBITDA за квартал из-за этого уменьшится примерно на €2 млн.',
     'quote': _ONTEX_Q3_QUOTE, 'url': ONTEX_Q3,
     'why': WHY + ': последствие указа для отчетности владельца'},

    # --- gf803c055 «Эвиосис Пэкэджинг Кубань» ---
    {'id': 'gf803c055', 'field': 'src', 'old': None,
     'new': ['Sec.gov', SONOCO], 'quote': _SONOCO_QUOTE, 'url': SONOCO,
     'why': WHY + ': квартальный отчет Sonoco (10-Q) — доля России в продажах и активах'},
    {'id': 'gf803c055', 'field': 'eco.share', 'old': '—',
     'new': '100% долей в уставном капитале ООО «Эвиосис Пэкэджинг Кубань»',
     'quote': '100 % долей в уставном капитале компании «Эвиосис Пэкэджинг Кубань»', 'url': URA,
     'why': WHY + ': доля, переданная в управление, — из текста указа; поле стояло пустым'},
    {'id': 'gf803c055', 'field': 'eco.context',
     'old': 'Завод специализируется на металлической таре для пищевых продуктов и раньше принадлежал международной группе Eviosys. В 2024 году ее купила американская Sonoco Products Company.',
     'new': 'Завод специализируется на металлической таре для пищевых продуктов и раньше принадлежал международной группе Eviosys. В 2024 году ее купила американская Sonoco Products Company. '
            'Российский бизнес принадлежит Sonoco через нидерландскую дочернюю компанию; за девять месяцев 2026 года на него пришлось около 1,1% продаж группы и около 0,7% ее активов. '
            'После указа Sonoco выясняет, потеряла ли она контроль над заводом и придется ли списывать гудвил и исключать компанию из отчетности.',
     'quote': _SONOCO_QUOTE + ' … The acquisition of Eviosys, Europe’s leading food cans, ends and closures manufacturer, for net cash consideration of approximately $3.8 billion on December 4, 2024.', 'url': SONOCO,
     'why': WHY + ': что указ значит для владельца, по его квартальному отчету'},

    # --- g38bdff94 ГМС / «Гидроиндустрия» ---
    {'id': 'g38bdff94', 'field': 'src', 'old': None,
     'new': ['Коммерсантъ', KOMM_GMS], 'quote': _GMS_NKR_QUOTE, 'url': KOMM_GMS,
     'why': WHY + ': полная газетная версия статьи «Коммерсанта» (в src была короткая лента)'},
    {'id': 'g38bdff94', 'field': 'eco.rationale',
     'old': 'Молчанов занимает пост гендиректора ГМС, а в прессе его называют одним из основателей группы; эксперты допускают, что именно эта роль могла определить сделку.',
     'new': 'Молчанов занимает пост гендиректора ГМС, а в прессе его называют одним из основателей группы. '
            'По мнению Екатерины Токаревой (Pen & Paper), долю он получил за то, что руководит группой, налаживал ее бизнес и будет ее развивать. '
            'Александр Тихов из «Аверта Групп» считает, что сделка завершает переход актива из иностранной собственности в российскую, а основатель в числе владельцев помогает удержать команду и инженерную экспертизу.',
     'quote': 'Господин Молчанов — гендиректор ГМС, в СМИ его также называют одним из основателей группы. … '
              'Руководитель отдела финансово-экономической экспертизы «Аверта Групп» Александр Тихов считает, что передача 49% в «Гидроиндустрии» Артему Молчанову завершает процедуру по выведению актива из иностранного контура в российский. '
              'По его словам, для машиностроительного актива с узкой инженерной компетенцией сохранение основателя в капитале удерживает команду и профильную экспертизу при смене собственника. '
              'Партнер Pen & Paper Екатерина Токарева полагает, что передача доли могла быть связана с ролью Артема Молчанова в управлении группой, налаживании бизнеса, а также в развитии компании в будущем.',
     'url': KOMM_GMS, 'why': WHY + ': мнения экспертов названы по именам'},
    {'id': 'g38bdff94', 'field': 'eco.target_fin',
     'old': 'По отчетности ГМС за 2024 год выручка группы выросла на 54%, до 95,5 млрд ₽, а EBITDA — на 47%, до 12,6 млрд ₽, частично благодаря СПГ-проектам. Основной производственный актив группы — «Гидромашсервис», выпускающий насосы и компрессоры для нефтегазовой отрасли, энергетики, коммунального хозяйства, металлургии, химии и судостроения.',
     'new': 'По отчетности ГМС за 2024 год выручка группы выросла на 54%, до 95,5 млрд ₽, а EBITDA — на 47%, до 12,6 млрд ₽, частично благодаря СПГ-проектам. Основной производственный актив группы — «Гидромашсервис», выпускающий насосы и компрессоры для нефтегазовой отрасли, энергетики, коммунального хозяйства, металлургии, химии и судостроения. '
            'Агентство НКР в сентябре 2026 года писало, что к апрелю 2026 года у «Гидромашсервиса» было подписано контрактов на 72 млрд ₽ — на 27% меньше, чем годом раньше: крупные СПГ-проекты завершаются. '
            'Вернуть выручку к уровню 2024 года агентство ожидает не раньше 2027 года.',
     'quote': _GMS_FIN_QUOTE + ' … ' + _GMS_NKR_QUOTE + ' … ' + _GMS_NKR2_QUOTE,
     'url': KOMM_GMS, 'why': WHY + ': портфель заказов главного актива по обзору НКР'},

    # --- g7bff6e5c Visiology ---
    {'id': 'g7bff6e5c', 'field': 'src', 'old': None,
     'new': ['АБН', ABN_VIS],
     'quote': 'Российский разработчик платформы бизнес-аналитики Visiology завершил инвестиционный раунд объемом 200 млн рублей.',
     'url': ABN_VIS, 'why': WHY + ': второе сообщение о закрытии раунда, со словами организатора'},
    {'id': 'g7bff6e5c', 'field': 'extra', 'old': None,
     'new': 'Первое полугодие 2026 года компания закончила с чистой прибылью и EBITDA выше плана. '
            'Платформой пользуются больше 500 организаций, среди них «Роснефть», «Газпром», «Самолет», Positive Technologies, Федеральное казначейство и Минздрав.',
     'quote': 'Решениями компании пользуются более 500 организаций, среди них Роснефть, Газпром, «Самолет», Positive Technologies, Федеральное казначейство и Минздрав. '
              'По итогам первого полугодия 2026 года выручка компании превысила собственный план более чем на 30%. '
              'Компания завершила период с чистой прибылью и показала EBITDA выше запланированного уровня.',
     'url': ABN_VIS, 'why': WHY + ': итог полугодия и известные клиенты'},

    # --- ga5a7f3c1 Aspace ---
    {'id': 'ga5a7f3c1', 'field': 'src', 'old': None,
     'new': ['Телеграм-канал @probonds', PROBONDS],
     'quote': 'Инвестор получит представительство в совете директоров и примет участие в реализации долгосрочной стратегии компании.',
     'url': PROBONDS, 'why': WHY + ': сообщение о сделке от компании (через канал организатора ее облигаций)'},
    {'id': 'ga5a7f3c1', 'field': 'law.terms', 'old': '—',
     'new': '«Атолл Капитал» получает место в совете директоров Aspace и будет участвовать в работе над долгосрочной стратегией компании.',
     'quote': 'В состав акционеров оператора гибких офисов ASPACE вошёл фонд прямых инвестиций « Атолл Капитал». '
              'Инвестор получит представительство в совете директоров и примет участие в реализации долгосрочной стратегии компании.',
     'url': PROBONDS, 'why': WHY + ': условие входа инвестора'},

    # --- ga09376f6 «Экспанта» / «Стаксель» ---
    {'id': 'ga09376f6', 'field': 'src', 'old': None,
     'new': ['ЕГРЮЛ: история участников ООО «СиЭс Технологии» (выгрузка Datanewton)', DN_STAKSEL],
     'quote': _DN_2026, 'url': DN_STAKSEL,
     'why': WHY + ': переход 25% к «Экспанте» записан в ЕГРЮЛ 23 октября 2026 года'},
    {'id': 'ga09376f6', 'field': 'src', 'old': None,
     'new': ['CNews', CNEWS_STAKSEL], 'quote': _CNEWS_TRANCHES, 'url': CNEWS_STAKSEL,
     'why': WHY + ': второе сообщение о сделке со словами сторон'},
    {'id': 'ga09376f6', 'field': 'date', 'old': '2026-10-19', 'new': '2026-10-23',
     'quote': _DN_2026, 'url': DN_STAKSEL,
     'why': WHY + ': доля в ООО переходит в момент записи в ЕГРЮЛ — 23 октября; 19 октября — день объявления'},
    {'id': 'ga09376f6', 'field': 'sum', 'old': 'Не раскрыта', 'new': '50 млн ₽',
     'quote': _RUSVEN_PRICE, 'url': RUSVEN_STAKSEL,
     'why': WHY + ': цена 25% названа в источнике карточки, но не была перенесена'},
    {'id': 'ga09376f6', 'field': 'eco.sum', 'old': '—', 'new': '50 млн ₽',
     'quote': _RUSVEN_PRICE, 'url': RUSVEN_STAKSEL, 'why': WHY + ': то же, что sum'},
    {'id': 'ga09376f6', 'field': 'eco.share', 'old': '—',
     'new': '25% ООО «СиЭс Технологии»; в течение четырех лет «Экспанта» может докупить еще 25%.',
     'quote': _RUSVEN_PRICE + ' … ' + _RUSVEN_USE, 'url': RUSVEN_STAKSEL,
     'why': WHY + ': размер пакета и право докупки'},
    {'id': 'ga09376f6', 'field': 'eco.val',
     'old': '«Экспанта» называет средневзвешенную оценку по двум траншам — 300 млн ₽. Цену самой доли компания не раскрыла.',
     'new': '«Экспанта» называет средневзвешенную оценку по двум траншам — 300 млн ₽. За первые 25% она заплатила 50 млн ₽.',
     'quote': _CNEWS_TRANCHES + ' … ' + _RUSVEN_PRICE + ' … ' + _RUSVEN_USE, 'url': RUSVEN_STAKSEL,
     'why': WHY + ': снята ложная фраза «цену доли не раскрыла» — цена названа'},
    {'id': 'ga09376f6', 'field': 'eco.fin', 'old': '—',
     'new': 'Половину денег «Экспанты» вложат в развитие «Стакселя» и запуск ИИ-агентов «Шкипер», вторую половину получит Владимир Скороход.',
     'quote': _RUSVEN_USE, 'url': RUSVEN_STAKSEL, 'why': WHY + ': куда идут деньги покупателя'},
    {'id': 'ga09376f6', 'field': 'law.struct',
     'old': 'Продавец — Владимир Скороход: по истории участников ЕГРЮЛ (проверено 19 октября 2026 года) он единственный участник ООО «СиЭс Технологии», ему принадлежат 100% с 25 мая 2018 года, уставный капитал — 10 тыс. ₽. Переход 25% к «Экспанте» в реестре пока не отражен. Сделка рассчитана на два транша: после второго доля «Экспанты» дойдет до 50%.',
     'new': 'Продавец — Владимир Скороход: по истории участников ЕГРЮЛ с 2018-05-25 он был единственным участником ООО «СиЭс Технологии» при уставном капитале 10 000 руб. '
            'Запись 2026-10-23 передала 25% «Экспанте», у Скорохода осталось 75%; уставный капитал не изменился, то есть доля куплена у владельца, а не выпущена заново. '
            'Сделка рассчитана на два транша: после второго доля «Экспанты» дойдет до 50%.',
     'quote': _DN_2018 + ' … ' + _DN_2026 + ' … ' + _CNEWS_TRANCHES + ' … Согласно данным сервиса проверки контрагентов Rusprofile , 75% в ООО “Сиэс Технологии” принадлежит Владимиру Скороходу.', 'url': DN_STAKSEL,
     'why': WHY + ': переход записан в реестре — снята фраза «в реестре пока не отражен»'},

    # --- g28941fd8 VEON / Perfectum ---
    {'id': 'g28941fd8', 'field': 'src', 'old': None,
     'new': ['Uzdaily.uz', UZDAILY], 'quote': _UZ_CLOSE, 'url': UZDAILY,
     'why': WHY + ': закрытие 27 октября по квартальному отчету VEON'},
    {'id': 'g28941fd8', 'field': 'src', 'old': None,
     'new': ['VEON (отчет 6-K, SEC)', VEON_6K],
     'quote': 'The transaction completed on October 27, 2026, and Perfectum will be consolidated from that date.',
     'url': VEON_6K, 'why': WHY + ': первоисточник — промежуточная отчетность VEON'},
    {'id': 'g28941fd8', 'field': 'status', 'old': 'Подписана', 'new': 'Закрыта',
     'quote': _UZ_CLOSE, 'url': UZDAILY, 'why': WHY + ': сделку закрыли 27 октября 2026 года'},
    {'id': 'g28941fd8', 'field': 'date', 'old': '2026-10-19', 'new': '2026-10-27',
     'quote': _UZ_CLOSE, 'url': UZDAILY, 'why': WHY + ': дата — день закрытия'},
    {'id': 'g28941fd8', 'field': 'title',
     'old': 'VEON покупает узбекского мобильного оператора Perfectum за $207 млн',
     'new': 'VEON купил узбекского мобильного оператора Perfectum за $207 млн',
     'quote': _UZ_CLOSE + ' … ' + _UZ_PRICE, 'url': UZDAILY,
     'why': WHY + ': время глагола — по статусу «Закрыта»'},
    {'id': 'g28941fd8', 'field': 'eco.fin', 'old': '—',
     'new': 'Продавцам VEON платит деньгами и передает здание; кроме того, договор обязывает VEON возместить продавцам часть других расходов.',
     'quote': _UZ_PRICE, 'url': UZDAILY, 'why': WHY + ': форма расчета из отчета VEON'},
    {'id': 'g28941fd8', 'field': 'eco.val',
     'old': 'В сумму $207 млн входит непогашенный долг Perfectum примерно на $93 млн, который VEON берет на себя. Остальное VEON закрывает своими деньгами, без привлечения внешнего финансирования.',
     'new': 'В сумму $207 млн входит непогашенный долг Perfectum примерно на $93 млн, который VEON берет на себя. Денежную часть VEON платит из собственных средств, без внешнего финансирования.',
     'quote': _UZ_PRICE + ' … The cash consideration will be funded from VEON’s existing cash resources.', 'url': UZDAILY,
     'why': WHY + ': «остальное деньгами» спорило с расчетом зданием — уточнено, что из своих средств только денежная часть'},
    {'id': 'g28941fd8', 'field': 'law.appr',
     'old': 'Регуляторы дали добро на сделку, но с условиями. Комитет по развитию конкуренции обязал Perfectum минимум три года после сделки работать как самостоятельный оператор, минимум 12 месяцев не менять действующие тарифы 5G FWA и не снижать среднюю скорость интернета ниже 300 Мбит/с; новому владельцу также запретили принуждать абонентов пользоваться сервисами Beeline и VEON и передавать их данные за рубеж. Стороны планируют закрыть сделку до конца октября 2026 года.',
     'new': 'Регуляторы дали добро на сделку, но с условиями. Комитет по развитию конкуренции обязал Perfectum минимум три года после сделки работать как самостоятельный оператор, минимум 12 месяцев не менять действующие тарифы 5G FWA и не снижать среднюю скорость интернета ниже 300 Мбит/с; новому владельцу также запретили принуждать абонентов пользоваться сервисами Beeline и VEON и передавать их данные за рубеж.',
     'quote': _SPOT_APPR_QUOTE + ' … Кроме того, запрещается принуждение к использованию цифровых платформ Beeline и VEON либо ограничение пользования конкурирующими сервисами.',
     'url': SPOT_APPR, 'why': WHY + ': снята устаревшая фраза о планах закрыть сделку — она закрыта'},

    # --- g32cfa1d4 Salmon ---
    {'id': 'g32cfa1d4', 'field': 'src', 'old': None,
     'new': ['Dealstreetasia.com', DSA],
     'quote': 'The financing round comprises $90 million in financing commitments from Spice Expeditions, Washington University Investment Management Company, Moore Strategic Ventures, and other existing backers.',
     'url': DSA, 'why': WHY + ': состав раунда'},
    {'id': 'g32cfa1d4', 'field': 'src', 'old': None,
     'new': ['En.antaranews.com', ANTARA],
     'quote': 'Salmon Group, a technology-driven banking and lending platform in the Philippines, today announces that it secured additional $140 million of financing to continue its growth in the Philippines.',
     'url': ANTARA, 'why': WHY + ': пресс-релиз компании (PRNewswire)'},
    {'id': 'g32cfa1d4', 'field': 'law.struct', 'old': '—',
     'new': '$90 млн — обязательства профинансировать компанию, которые дали Spice Expeditions, Washington University Investment Management Company, Moore Strategic Ventures и другие прежние инвесторы; еще $50 млн Salmon получила от публичного выпуска облигаций.',
     'quote': 'The financing round comprises $90 million in financing commitments from Spice Expeditions, Washington University Investment Management Company, Moore Strategic Ventures, and other existing backers. '
              'The remainder comprises a $50-million public bond issuance.',
     'url': DSA, 'why': WHY + ': как устроен раунд и кто в нем участвовал'},
    {'id': 'g32cfa1d4', 'field': 'eco.target_fin', 'old': '—',
     'new': 'Выручку и прибыль компания не раскрывает. Ее приложение скачали 9 млн раз.',
     'quote': 'Today, the companies in Salmon Group serve millions of Filipinos through its Salmon app – one of the highest rated financial services apps in the Philippines with 9 million downloads, 4.8 rating on App Store and Google Play, 99.9% uptime, and dedicated 24/7 customer support.',
     'url': ANTARA, 'why': WHY + ': масштаб компании — в абсолютных числах, которые она называет'},

    # --- g7d3f5a20 «Росатом» / DP World / FESCO ---
    {'id': 'g7d3f5a20', 'field': 'src', 'old': None,
     'new': ['Pravo.ru', PRAVO_FESCO],
     'quote': 'Руководить новой структурой назначена директор по развитию бизнеса госкорпорации Екатерина Ляхова, ранее она возглавляла УК «Дело».',
     'url': PRAVO_FESCO, 'why': WHY + ': кто руководит совместным предприятием'},
    {'id': 'g7d3f5a20', 'field': 'src', 'old': None,
     'new': ['Вгудок', VGUDOK],
     'quote': 'Юридическое оформление сделки, получившей одобрение ФАС и Правительственной комиссии по иностранным инвестициям, должно завершиться до конца 2026 года.',
     'url': VGUDOK, 'why': WHY + ': срок оформления, ноябрь 2026'},
    {'id': 'g7d3f5a20', 'field': 'law.struct',
     'old': 'Совместное предприятие — ООО «Глобальная логистика»: «Росатом» зарегистрировал его 24 декабря 2025 года и собирается передать ему 92,5% акций ДВМП. Госкорпорация оставит за собой 51%, DP World получит 49% за денежный взнос.',
     'new': 'Совместное предприятие — ООО «Глобальная логистика»: «Росатом» зарегистрировал его 24 декабря 2025 года и собирается передать ему 92,5% акций ДВМП. Госкорпорация оставит за собой 51%, DP World получит 49% за денежный взнос. '
            'Руководит «Глобальной логистикой» Екатерина Ляхова — директор «Росатома» по развитию бизнеса, раньше возглавлявшая УК «Дело».',
     'quote': 'Согласно данным ЕГРЮЛ, 24 декабря 2025 года «Росатом» зарегистрировал ООО «Глобальная логистика». В это совместное предприятие планируется внести 92,5% акций ДВМП. Российская сторона сохранит 51%, арабская получит 49% в обмен на денежный вклад. … '
              'Руководить новой структурой назначена директор по развитию бизнеса госкорпорации Екатерина Ляхова, ранее она возглавляла УК «Дело».',
     'url': PRAVO_FESCO, 'why': WHY + ': руководитель совместного предприятия'},
    {'id': 'g7d3f5a20', 'field': 'extra', 'old': None,
     'new': 'В ноябре 2026 года отраслевое издание Вгудок писало, что юридически сделку должны оформить до конца 2026 года, а деньги DP World не станут платой «Росатому» за пакет: они останутся в совместной компании и пойдут на ее инвестиционную программу.',
     'quote': 'Принципиальный момент конфигурации заключается в том, что арабская сторона оплачивает свою долю живыми деньгами, однако эти средства не уходят в доход Росатома как плата за актив, а остаются внутри совместной компании. '
              'Фактически речь идёт о масштабной докапитализации создаваемого холдинга для реализации внушительной инвестиционной программы. '
              'Юридическое оформление сделки, получившей одобрение ФАС и Правительственной комиссии по иностранным инвестициям, должно завершиться до конца 2026 года.',
     'url': VGUDOK, 'why': WHY + ': ожидаемый срок закрытия и куда идут деньги, по версии издания'},
]
