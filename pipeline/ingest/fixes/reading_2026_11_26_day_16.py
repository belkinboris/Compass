# -*- coding: utf-8 -*-
"""Дневной обыск 26 ноября 2026, партия day_16 (REVISION_BRIEF.md, первый уровень).

Поиск источников:
  gee7be9ef (IBS/Luxoft) — AIN, Сноб, JD Supra, Compliance Week: санкции США против
    Карачинского 20.04.2022 (день перехода долей), самораскрытие DXC и предупреждения
    OFAC/BIS вместо штрафа (2024), часть команды ушла в IT_One; пресс-релиз DXC — выход
    сокращает выручку на ~$140 млн в год. ИНН/выручку «Люксофт Профешнл», консультантов,
    10-K DXC (sec.gov 403) — не нашли.
  g070084ad (Вяртсиля Восток) — финансы перенесены из «Контекста» в eco.target_fin;
    иск Северной верфи, доля России у Wärtsilä; переименование в «В-Восток» 01.08.2022
    подтверждено историей ЕГРЮЛ (Датаньютон, ОГРН 5067847118389) — в текст не пишется.
  g887ba980 (Транзас Навигатор) — ДП 2023 и 2025: продукция, выручка 2022–2024.
  ga024ea1e (Pizza Hut/Ной-М) — отчет AmRest за I полугодие 2022: 31 мая передано 59
    пиццерий (19 своих, 40 франчайзи); финансы «Амрест Пиццы» 2021 и «ПиццаН» 2024.
  g19f07141 (Kingspan) — Irish Times 2023: расход €16,5 млн на продажу; ДП 2022: финансы
    ООО «Кингспан» 2020, единственный участник «Ф109 лимитед».
"""

WHY = 'дневной обыск 26 ноября 2026 (партия day_16)'

FIXES = [{'id': 'gee7be9ef',
  'field': 'src',
  'old': None,
  'new': ['AIN', 'https://en.ain.ua/2022/04/26/luxoft-transfers-business-to-ibs'],
  'quote': 'Besides, some of Luxoft’s employees in Russia have moved to IT_One. This company is controlled '
           'by another Luxoft co-founder, Sergey Matsotsky.',
  'url': 'https://en.ain.ua/2022/04/26/luxoft-transfers-business-to-ibs',
  'why': 'дневной обыск 26 ноября 2026 (партия day_16); часть сотрудников ушла в IT_One Мацоцкого; '
         'численность в России'},
 {'id': 'gee7be9ef',
  'field': 'src',
  'old': None,
  'new': ['Сноб',
          'https://snob.ru/news/shvejcarskij-razrabotchik-luxoft-peredal-rossijskie-aktivy-gruppe-kompanij-ibs/'],
  'quote': '20 апреля Карачинского включили в санкционные списки США как члена наблюдательного совета банка '
           '«Открытие», который тоже находится под санкциями.',
  'url': 'https://snob.ru/news/shvejcarskij-razrabotchik-luxoft-peredal-rossijskie-aktivy-gruppe-kompanij-ibs/',
  'why': 'дневной обыск 26 ноября 2026 (партия day_16); санкции США против Карачинского в день перехода '
         'долей'},
 {'id': 'gee7be9ef',
  'field': 'src',
  'old': None,
  'new': ['JD Supra', 'https://www.jdsupra.com/legalnews/dxc-technology-company-settles-2208672/'],
  'quote': 'The underlying violations purportedly stem from the sale of DXC subsidiary Luxoft’s Russian '
           'Federation-based operations to IBS Holding LLC (“IBS Holding”) in April 2022, following the '
           'Putin regime’s invasion of Ukraine.',
  'url': 'https://www.jdsupra.com/legalnews/dxc-technology-company-settles-2208672/',
  'why': 'дневной обыск 26 ноября 2026 (партия day_16); предупреждения OFAC и BIS вместо штрафа по этой '
         'продаже'},
 {'id': 'gee7be9ef',
  'field': 'src',
  'old': None,
  'new': ['CNews', 'https://zoom.cnews.ru/news/item/554837'],
  'quote': 'В апреле 2022 г. группа IBS выкупила обратно российский бизнес Luxoft – ООО «Люксфот профешенел» '
           'и АНО «Учебный центр Люксофт».',
  'url': 'https://zoom.cnews.ru/news/item/554837',
  'why': 'дневной обыск 26 ноября 2026 (партия day_16); масштаб российского бизнеса: выручка, люди, центры '
         'разработки'},
 {'id': 'gee7be9ef',
  'field': 'eco.target_fin',
  'old': '—',
  'new': 'DXC оценила, что из-за ухода из России будет недополучать около $140 млн выручки в год — меньше 1% '
         'своей годовой выручки; в России у нее работали около 4 тыс. человек. Центры разработки Luxoft в '
         'России были в Москве, Санкт-Петербурге, Дубне, Нижнем Новгороде и Омске.',
  'quote': 'Американская аутсорсинговая ИТ-компания DXC Technology, купившая в 2019 г. Luxoft, из-за ухода '
           'из России потеряет ежегодный доход в размере $140 млн. … Это менее 1% ее годовой выручки. В '
           'России у компании работало 4 тыс. … В России центры разработки Luxoft находились в Москве , '
           'Санкт-Петербурге , подмосковной Дубне , Нижнем Новгороде и Омске .',
  'url': 'https://zoom.cnews.ru/news/item/554837',
  'why': 'дневной обыск 26 ноября 2026 (партия day_16); масштаб российского бизнеса по оценке продавца '
         '(CNews по отчетности DXC)'},
 {'id': 'gee7be9ef',
  'field': 'eco.context',
  'old': 'Luxoft основали в 2000 году, среди учредителей был Анатолий Карачинский. IBS была крупнейшим '
         'акционером Luxoft и в 2019 году продала свою долю американской DXC Technology (сделка на $2 млрд). '
         'Теперь российское юрлицо вернулось в группу IBS. 25 мая 2022 года DXC сообщила, что после '
         'окончания квартала вышла из внутреннего российского бизнеса.',
  'new': 'Luxoft основали в 2000 году Анатолий Карачинский и Сергей Мацоцкий, создатели IBS. В 2019 году '
         'IBS, тогда крупнейший акционер Luxoft, уступила свой пакет американской DXC Technology за $2 млрд; '
         'теперь российское юрлицо вернулось в группу. Часть российских сотрудников Luxoft ушла в IT_One, '
         'которую контролирует Мацоцкий. В день перехода долей, 20 апреля 2022 года, США внесли Карачинского '
         'в свой санкционный список — он входил в набсовет банка «Открытие». 25 мая 2022 года DXC сообщила, '
         'что после окончания квартала вышла из внутреннего российского бизнеса. Позже DXC сама сообщила '
         'американским регуляторам о возможных нарушениях санкций и экспортного контроля при этой продаже; в '
         '2024 году OFAC и Бюро промышленности и безопасности Минторга США ограничились предупредительными '
         'письмами без штрафов.',
  'quote': 'Luxoft была создана в 2000 году основателями IBS Анатолием Карачинским и Сергеем Мацоцким. … '
           'Ранее IBS была крупнейшим акционером Luxoft, пока в 2019 году не продала свою долю американской '
           'компании DXC Technology. Сумма сделки составила $2 миллиарда. … Besides, some of Luxoft’s '
           'employees in Russia have moved to IT_One. This company is controlled by another Luxoft '
           'co-founder, Sergey Matsotsky. … on April 20, Cyprus-based Luxoft International transferred 100% '
           'of the Russian legal entity to IBS IT Services LLC and IBS LLC … 20 апреля Карачинского включили '
           'в санкционные списки США как члена наблюдательного совета банка «Открытие», который тоже '
           'находится под санкциями. … Subsequent to the end of the quarter, DXC exited its domestic Russian '
           'business. … discuss these results on May 25, 2022, at 5:00 p.m. EDT … On May 17, 2024, '
           'Nevada-based DXC Technology Company … According to the SEC filing, DXC officially submitted its '
           'final voluntary self-disclosures to OFAC in August 2023 and to BIS in November 2023. Thereafter, '
           'both OFAC and BIS issued warning/cautionary letters to DXC in lieu of the assessment of any '
           'administrative penalties. The underlying violations purportedly stem from the sale of DXC '
           'subsidiary Luxoft’s Russian Federation-based operations to IBS Holding LLC (“IBS Holding”) in '
           'April 2022',
  'url': 'https://www.jdsupra.com/legalnews/dxc-technology-company-settles-2208672/',
  'why': 'дневной обыск 26 ноября 2026 (партия day_16); санкции против Карачинского в день сделки, '
         'самораскрытие DXC и предупреждения OFAC/BIS, уход части команды в IT_One'},
 {'id': 'g070084ad',
  'field': 'eco.target_fin',
  'old': '—',
  'new': 'Выручка за 2021 год — 3,6 млрд ₽, на 405 млн ₽ больше, чем годом ранее; чистая прибыль — 227 млн '
         '₽. По госзакупкам среди крупнейших заказчиков — «Атомфлот», «Газпром флот», Балтийский завод, '
         '«Транснефть-Восток» и «РН-Пурнефтегаз».',
  'quote': 'в 2021 году выручка ООО "Вяртсиля Восток" выросла на 405 млн, до 3,6 млрд рублей, чистая прибыль '
           'составила 227 млн, говорится в данных СПАРК. … По данным Rusprofile, "Вяртсиля Восток" активно '
           'работала на рынке российских госзакупок, в числе её крупнейших контрагентов — Балтийский завод , '
           '"РН–Пурнефтегаз", "Транснефть–Восток", " Газпром Флот ", а также ФГУП " Атомфлот ".',
  'url': 'https://www.dp.ru/a/2022/07/15/Kak_v_more_korabli',
  'why': 'дневной обыск 26 ноября 2026 (партия day_16); финансы предмета лежали в «Контексте» — перенесены в '
         'свое поле'},
 {'id': 'g070084ad',
  'field': 'eco.context',
  'old': '«Вяртсиля Восток» обслуживает судовое оборудование. В 2021 году выручка выросла на 405 млн ₽, до '
         '3,6 млрд ₽, чистая прибыль — 227 млн ₽. Новый владелец — 42-летний Константин Норцев, который '
         'работал в Wärtsilä больше 15 лет и с сентября 2020 года руководил «Вяртсиля Восток». Компания '
         'продолжает работу под названием V-Vostok (ООО «В-Восток»). Тогда же Wärtsilä продала местным '
         'менеджерам «Транзас Навигатор» и закрыла петербургский офис Wärtsilä Digital Technologies.',
  'new': '«Вяртсиля Восток» поставляла российским заказчикам судовое оборудование и проектировала '
         'гражданские суда; по ее проекту завод «Янтарь» строит траулер «Виктор Гаврилов». Новый владелец — '
         '42-летний Константин Норцев: он больше 15 лет работал в Wärtsilä и с сентября 2020 года руководил '
         '«Вяртсиля Восток». После сделки компания называется ООО «В-Восток» и обслуживает судовое '
         'оборудование. На Россию в 2021 году приходилось около 5% чистых продаж Wärtsilä. В мае 2022 года '
         'Северная верфь требовала через суд, чтобы «Вяртсиля Восток» исполнила обязательства по поставкам, '
         'но затем от иска отказалась. Тогда же Wärtsilä продала местным менеджерам «Транзас Навигатор» и '
         'закрыла петербургский офис Wärtsilä Digital Technologies.',
  'quote': '"Вяртсиля Восток" занимается поставками оборудования для российских заказчиков, а также '
           'разработкой проектов гражданских судов. По одному из них (5670WSD) ПСЗ "Янтарь" строит '
           'рыболовный морозильный траулер "Виктор Гаврилов" … По данным газеты, 42–летний Константин Норцев '
           '… В Wärtsilä он работает больше 15 лет, в сентябре 2020–го возглавил "Вяртсиля Восток". … На '
           'деятельность, связанную с нашей страной, в 2021 году пришлось около 5% чистых продаж Wärtsilä … '
           'Вскоре после этого, в мае, Северная верфь подала иск к ООО "Вяртсиля Восток" о понуждении к '
           'исполнению обязательств в натуре. Детали этого дела стороны не разглашали, а впоследствии верфь '
           'отказалась от судебного разбирательства. А летом 2022–го Балтийский завод подал иск … The team '
           'previously working for Wärtsilä Vostok LLC continues under a newly established company, V-Vostok '
           'LLC, which will continue to provide marine equipment maintenance services locally. … In '
           'May/June, Wärtsilä signed agreements to sell the Transas Navigator business and Wärtsilä Vostok '
           'LLC to the local management of the companies. … As part of the exit, the Wärtsilä Digital '
           'Technologies (WDT) office in Saint Petersburg has been closed.',
  'url': 'https://www.dp.ru/a/2022/07/15/Kak_v_more_korabli',
  'why': 'дневной обыск 26 ноября 2026 (партия day_16); финансы ушли в eco.target_fin; добавлены профиль '
         'компании, доля России у Wärtsilä, иск Северной верфи'},
 {'id': 'g070084ad',
  'field': 'eco.val',
  'old': 'Цена не раскрывалась; оценить ее нельзя, потому что условия неизвестны — в том числе есть ли у '
         'прежнего владельца право обратного выкупа.',
  'new': 'Цена не раскрывалась. В инвестиционных кругах оценить ее не взялись: неизвестны условия, в том '
         'числе есть ли у прежнего владельца право обратного выкупа. Wärtsilä сообщила, что финансовые '
         'последствия продаж в России укладываются в резервы, созданные в I квартале 2022 года, и на '
         'результаты II квартала заметно не повлияли.',
  'quote': 'Собеседники "ДП" в инвестиционных кругах затруднились с оценкой возможной стоимости сделки, '
           'поскольку неизвестны её условия: например, есть ли у "материнской" компании право обратного '
           'выкупа. … following its announcement of scaling down activities in April 2022. … The financial '
           'impact of these divestments is in line with the provisions taken in the first quarter of 2022 '
           'and therefore do not have material impact on Wärtsilä’s Q2 financials.',
  'url': 'https://www.wartsila.com/media/news/21-07-2022-wartsila-completes-russian-market-exit-3130664',
  'why': 'дневной обыск 26 ноября 2026 (партия day_16); итог продажи для продавца — в пределах резервов I '
         'квартала (пресс-релиз Wärtsilä)'},
 {'id': 'g887ba980',
  'field': 'src',
  'old': None,
  'new': ['ДП', 'https://www.dp.ru/a/2023/03/10/V_more_golfa'],
  'quote': 'Петербургский производитель оборудования для морской навигации ООО "Транзас Навигатор" теперь '
           'полностью принадлежит предпринимателю Дмитрию Лагутину.',
  'url': 'https://www.dp.ru/a/2023/03/10/V_more_golfa',
  'why': 'дневной обыск 26 ноября 2026 (партия day_16); профиль компании и консолидация долей у Лагутина'},
 {'id': 'g887ba980',
  'field': 'src',
  'old': None,
  'new': ['ДП', 'https://www.dp.ru/a/2025/04/16/bivshaja-dochka-waertsilae-vosstanovila'],
  'quote': 'Выручка "Транзас Навигатора" за 2022 год составила 2,3 млрд, за 2023–й — 1,4 млрд.',
  'url': 'https://www.dp.ru/a/2025/04/16/bivshaja-dochka-waertsilae-vosstanovila',
  'why': 'дневной обыск 26 ноября 2026 (партия day_16); выручка компании после сделки'},
 {'id': 'g887ba980',
  'field': 'eco.target_fin',
  'old': '—',
  'new': 'Компания делает оборудование для морской навигации (среди заказов — СПГ-танкеры для «Арктик СПГ '
         '2»), тренажеры для обучения моряков и электронные карты. Выручка в 2022 году — 2,3 млрд ₽, в '
         '2023-м — 1,4 млрд ₽, в 2024-м — 1,9 млрд ₽.',
  'quote': 'Петербургский производитель оборудования для морской навигации ООО "Транзас Навигатор" … В '
           'последние годы "Транзас Навигатор" производил навигационные системы для СПГ–танкеров, которые " '
           'Новатэк " строит для проекта "Арктик СПГ 2", виртуальные тренажёры для моряков и '
           'картографические сервисы для судовладельцев. … Частные петербургские компании, занятые '
           'разработкой и производством оборудования морской навигации и связи, а также софта для него, '
           'опубликовали финансовые результаты за 2024 год Самой успешной оказалась бывшая "дочка" '
           'финляндской Wärtsilä Voyage Limited — ООО "Транзас Навигатор", она заработала 1,9 млрд рублей. … '
           'Выручка "Транзас Навигатора" за 2022 год составила 2,3 млрд, за 2023–й — 1,4 млрд.',
  'url': 'https://www.dp.ru/a/2025/04/16/bivshaja-dochka-waertsilae-vosstanovila',
  'why': 'дневной обыск 26 ноября 2026 (партия day_16); масштаб предмета: продукция и выручка'},
 {'id': 'g887ba980',
  'field': 'eco.val',
  'old': 'Цена не раскрывалась.',
  'new': 'Цена не раскрывалась. Wärtsilä сообщила, что финансовые последствия продаж в России укладываются в '
         'резервы, созданные в I квартале 2022 года, и на результаты II квартала заметно не повлияли.',
  'quote': 'following its announcement of scaling down activities in April 2022. … The financial impact of '
           'these divestments is in line with the provisions taken in the first quarter of 2022 and '
           'therefore do not have material impact on Wärtsilä’s Q2 financials.',
  'url': 'https://www.wartsila.com/media/news/21-07-2022-wartsila-completes-russian-market-exit-3130664',
  'why': 'дневной обыск 26 ноября 2026 (партия day_16); итог продажи для продавца — в пределах резервов I '
         'квартала (пресс-релиз Wärtsilä)'},
 {'id': 'ga024ea1e',
  'field': 'src',
  'old': None,
  'new': ['AmRest', 'https://www.amrest.eu/en/media/download/2302'],
  'quote': 'This transfer has led to the exit of 59 restaurants, 19 equity and 40 franchised.',
  'url': 'https://www.amrest.eu/en/media/download/2302',
  'why': 'дневной обыск 26 ноября 2026 (партия day_16); отчет продавца за I полугодие 2022: дата передачи и '
         'число пиццерий'},
 {'id': 'ga024ea1e',
  'field': 'eco.target_fin',
  'old': '—',
  'new': 'Прежний оператор сети, ООО «Амрест Пицца», за 2021 год получил 362 млн ₽ выручки (на 25% меньше, '
         'чем годом ранее) и 161 млн ₽ чистого убытка. У «ПиццаН» в 2024 году выручка — 233 млн ₽ (минус '
         '7%), чистый убыток — 11,9 млн ₽.',
  'quote': 'По данным Kartoteka.ru, в 2021 году выручка прежнего владельца сети ООО «Амрест Пицца» упала на '
           '25%, до 362 млн руб., чистый убыток составил 161 млн руб. … Финансовые показатели «ПиццаН» '
           'ухудшаются: по данным за 2024 год, выручка упала на 7% до 233 млн рублей, а компания закончила '
           'год с чистым убытком в 11,9 млн рублей.',
  'url': 'https://www.kommersant.ru/doc/5392616',
  'why': 'дневной обыск 26 ноября 2026 (партия day_16); финансы сети до и после сделки'},
 {'id': 'ga024ea1e',
  'field': 'law.terms',
  'old': 'По сведениям на 7 июня 2022 года сделка уже была закрыта; Yum! Brands объявила о завершении '
         'передачи бизнеса Pizza Hut местному оператору 5 июля 2022 года.',
  'new': 'Переговоры о передаче сети местному оператору AmRest вела с Yum! Brands и отчитывалась о них за I '
         'квартал 2022 года. Мастер-франшизное соглашение AmRest по России прекратилось в конце мая, и в тот '
         'же день все российские пиццерии сети — собственные и франчайзинговые — перешли к оператору, '
         'которого выбрала Yum! Brands. О завершении передачи Yum! Brands объявила в начале июля.',
  'quote': 'Владелец мастер-франшизы Pizza Hut в России Amrest сообщил в своей отчетности за первый квартал '
           '2022 года, что ведет переговоры с владельцем бренда — Yum! Brands о передаче сети пиццерий в РФ '
           'местному оператору. … the reason for the decrease in the total number of units has been the '
           'transfer on 31 May of all the Pizza Hut restaurants located in Russia to a third party '
           'designated by YUM! and the termination of the Master Franchise Agreement (MFA) for this market, '
           'as previously agreed. This transfer has led to the exit of 59 restaurants, 19 equity and 40 '
           'franchised. … Senior Editor July 5, 2022 … Yum Brands announced it has completed the transfer of '
           'ownership of all Pizza Hut locations to a new owner',
  'url': 'https://www.amrest.eu/en/media/download/2302',
  'why': 'дневной обыск 26 ноября 2026 (партия day_16); порядок передачи по отчету продавца вместо «по '
         'сведениям на 7 июня сделка уже закрыта»'},
 {'id': 'g19f07141',
  'field': 'src',
  'old': None,
  'new': ['The Irish Times',
          'https://www.irishtimes.com/business/2023/02/17/kingspan-grew-revenue-and-profit-last-year-despite-bumpy-conditions'],
  'quote': 'The accounts showed the group recorded a non-trading charge of €16.5 million in the year over '
           'its net loss on the divestment of its Russian operations.',
  'url': 'https://www.irishtimes.com/business/2023/02/17/kingspan-grew-revenue-and-profit-last-year-despite-bumpy-conditions',
  'why': 'дневной обыск 26 ноября 2026 (партия day_16); убыток Kingspan от продажи по годовой отчетности'},
 {'id': 'g19f07141',
  'field': 'src',
  'old': None,
  'new': ['ДП', 'https://www.dp.ru/a/2022/04/06/Minus_dvoe_iz_Lenoblasti'],
  'quote': 'Её единственный учредитель — "Ф109 лимитед", говорится в данных ЕГРЮЛ.',
  'url': 'https://www.dp.ru/a/2022/04/06/Minus_dvoe_iz_Lenoblasti',
  'why': 'дневной обыск 26 ноября 2026 (партия day_16); финансы ООО «Кингспан», покупатель по ЕГРЮЛ'},
 {'id': 'g19f07141',
  'field': 'eco.target_fin',
  'old': '—',
  'new': 'Выручка ООО «Кингспан» за 2020 год — 1,8 млрд ₽, на 14% меньше, чем годом ранее; чистая прибыль — '
         '36 млн ₽ (минус 70%).',
  'quote': 'По данным ФНС , выручка ООО "Кингспан" в 2020 году сократилась на 14% до 1,8 млрд, чистая '
           'прибыль снизилась на 70% до 36 млн рублей (данные за прошлый год пока не опубликованы).',
  'url': 'https://www.dp.ru/a/2022/04/06/Minus_dvoe_iz_Lenoblasti',
  'why': 'дневной обыск 26 ноября 2026 (партия day_16); финансы предмета'},
 {'id': 'g19f07141',
  'field': 'eco.val',
  'old': 'Цена не раскрывалась; по данным The Irish Times, Kingspan получила по сделке небольшой убыток.',
  'new': 'Цена не раскрывалась. По данным The Irish Times, Kingspan ожидала по сделке небольшой убыток; '
         'позже в годовой отчетности компания отразила по продаже российского бизнеса разовый расход.',
  'quote': 'It is understood that the Cavan-based multinational faces a small loss on the deal. … The '
           'accounts showed the group recorded a non-trading charge of €16.5 million in the year over its '
           'net loss on the divestment of its Russian operations.',
  'url': 'https://www.irishtimes.com/business/2023/02/17/kingspan-grew-revenue-and-profit-last-year-despite-bumpy-conditions',
  'why': 'дневной обыск 26 ноября 2026 (партия day_16); размер убытка продавца по годовой отчетности'}]
