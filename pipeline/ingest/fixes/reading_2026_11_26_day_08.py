# -*- coding: utf-8 -*-
"""Дневной обыск 26 ноября 2026, партия day_08 (REVISION_BRIEF.md, первый уровень).

Карточки: g09b38753, g6797d158, g4fb4d8b0, ge0af58de, g083ec8ce.

Поиск источников:
  g09b38753 (DEPO/«Кванто Спейс») — шесть запросов (стороны+предмет, новый
    владелец, ABR technology, реквизиты «Кванто Спейс», Telegram, суды и иск о
    конфискации): кроме CNews (и его зеркала zoom.cnews.ru в битой кодировке)
    ничего о сделке нет. Ничего не записано.
  g6797d158 (Halliburton/«БурСервис») — отчет Halliburton 10-Q за III квартал
    2022 года (письмо о намерениях в мае 2022), интервью Интерфакса с
    председателем совета директоров «БурСервиса» Р. Ждановым (правопреемство
    по всем обязательствам и контрактам), Прайм (ходатайство АО «Бурсервис» о
    покупке «Нафта Дриллинг Компани»). Записаны law.terms, law.struct, src.
  g4fb4d8b0 (Новатэк/«Тернефтегаз») — The National (причина продажи:
    месторождение законсервировано в первом полугодии), Reuters (публикация
    Le Monde и Global Witness об авиатопливе, ответ TotalEnergies, ее 19,4% в
    «Новатэке»), LNG Prime, Upstream. Дата закрытия не найдена. Записаны
    eco.rationale, src.
  ge0af58de (Дело/Global Ports) — пресс-релиз Maersk 29.08.2022 (причина
    продажи), Прайм о результатах Global Ports за 2021 год. 135 млн $ из
    годового отчета Maersk уже подтверждены PortNews в src. Записаны
    eco.rationale, eco.target_fin, src.
  g083ec8ce (Raisio/Copacker Agro) — сообщение Raisio 29.04.2022 (причина
    продажи), Retail.ru (своего производства в России не было), Инк.
    (русское имя покупателя ООО «Копэкер Агро», Серпухов, 2016 год, финансы
    покупателя). Записаны buyer_name, eco.rationale, eco.context, law.struct, src.

Запуск: python3 pipeline/ingest/review.py  (сухой прогон; запись — старший)
"""

WHY = 'дневной обыск 26 ноября 2026 (партия day_08)'

CARDS = ['g09b38753', 'g6797d158', 'g4fb4d8b0', 'ge0af58de', 'g083ec8ce']

_HAL_10Q = 'https://www.sec.gov/Archives/edgar/data/45012/000004501222000067/hal-20220930.htm'
_HAL_IFX = 'https://interfax.com/newsroom/exclusive-interviews/106943/'
_HAL_PRIME = 'https://1prime.ru/20241216/halliburton-853600513.html'
_SNOB = 'https://snob.ru/news/nefteservisnaya-kompaniya-halliburton-ushla-iz-rossii/'

_TTE_NAT = 'https://www.thenationalnews.com/business/energy/2022/08/26/totalenergies-sells-its-49-stake-in-russian-oil-company-terneftegaz-to-novatek'
_TTE_REU = 'https://ca.finance.yahoo.com/news/totalenergies-involved-jet-fuel-supply-105147550.html'
_TTE_LNG = 'https://lngprime.com/asia/novatek-becomes-sole-owner-of-russian-gas-field-after-totalenergies-deal/60173'
_TTE_UPS = 'https://www.upstreamonline.com/news/2-1-1286021'

_MAERSK = 'https://www.maersk.com/news/articles/2022/08/29/maersk-divests-its-share-in-global-ports'
_GP_PRIME = 'https://1prime.ru/20220303/836249986.html'

_RAI_APR = 'https://news.cision.com/raisio-oyj/r/raisio-plc-to-sell-its-russian-consumer-business-and-recognise-impairment-losses,c3557123'
_RAI_MAY = 'https://news.cision.com/raisio-oyj/r/raisio-plc-s-consumer-business-in-russia-transferred-to-the-new-owner,c3566481'
_RAI_IFX = 'https://interfax.com/newsroom/top-stories/79090/'
_RAI_RETAIL = 'https://www.retail.ru/news/finskaya-kompaniya-raisio-prodala-rossiyskiy-biznes-14-maya-2022-216683'
_RAI_INC = 'https://incrussia.ru/news/nordic-rossijskij-biznes/'

FIXES = [
    # ---------------- g6797d158 — Halliburton / «БурСервис»
    {'id': 'g6797d158', 'field': 'src', 'old': None,
     'new': ['Halliburton (отчет 10-Q за III квартал 2022)', _HAL_10Q],
     'quote': 'We executed a non-binding letter of intent with the Russia based management team in May of 2022 for the divestiture of the Russian operations.',
     'url': _HAL_10Q,
     'why': WHY + '; отчетность продавца: письмо о намерениях в мае 2022 года, завершение в III квартале'},
    {'id': 'g6797d158', 'field': 'src', 'old': None,
     'new': ['Интерфакс (интервью Романа Жданова)', _HAL_IFX],
     'quote': 'The company became a legal successor of all assets and contracts of the U.S.-based Halliburton after its departure from Russia.',
     'url': _HAL_IFX,
     'why': WHY + '; покупатель о правопреемстве по обязательствам и контрактам Halliburton'},
    {'id': 'g6797d158', 'field': 'src', 'old': None,
     'new': ['Прайм', _HAL_PRIME],
     'quote': 'В сентябре 2022 года "Бурсервис" приобрела права на оказание нефтесервисных услуг в части всего бизнеса Halliburton в России.',
     'url': _HAL_PRIME,
     'why': WHY + '; «Бурсервис» (АО) как преемник российского бизнеса Halliburton'},
    {'id': 'g6797d158', 'field': 'law.terms',
     'old': 'Условия сделки Halliburton не раскрыла.',
     'new': 'Необязывающее письмо о намерениях Halliburton подписала с российской командой управленцев в мае 2022 года, а продажу завершила в третьем квартале. Цену и прочие условия компания не называла.',
     'quote': 'We executed a non-binding letter of intent with the Russia based management team in May of 2022 for the divestiture of the Russian operations. … During the third quarter of 2022, we completed the sale of our Russia operations to a Russia-based management team made up of former Halliburton employees.',
     'url': _HAL_10Q,
     'why': WHY + '; порядок сделки из отчета 10-Q'},
    {'id': 'g6797d158', 'field': 'law.struct',
     'old': 'По данным ЕГРЮЛ, с 8 сентября 2022 года ООО «Апстрим Сервисес», которым раньше полностью владела нидерландская структура Halliburton, принадлежит ООО «БурСервис», а 95% «БурСервиса» — самому «Апстрим Сервисес». За этой конструкцией, по словам Halliburton, стоят ее бывшие российские управленцы.',
     'new': 'По данным ЕГРЮЛ, с 8 сентября 2022 года ООО «Апстрим Сервисес», которым раньше полностью владела нидерландская структура Halliburton, принадлежит ООО «БурСервис», а 95% «БурСервиса» — самому «Апстрим Сервисес». За этой конструкцией, по словам Halliburton, стоят ее бывшие российские управленцы. Позже председатель совета директоров «БурСервиса» Роман Жданов говорил, что компания приняла на себя все обязательства Halliburton в России, включая контракты, и скрытых обязательств у нее нет.',
     'quote': 'РБК отметил , что с 8 сентября текущего года 95% ООО «БурСервис» принадлежит ООО «Апстрим Сервисес», которая с того же дня полностью находится в собственности ООО «БурСервис». … Также издание пишет, что ранее 100% «Апстрим Сервисес» владела зарегистрированная в Нидерландах Halliburton. … 9 сентября 2022 г. … The Russia-based management team now owns and operates our former business and assets in Russia under the name BurService LLC, which is independent from Halliburton. … Exclusive Interviews 4 Nov 2024 BurService Board Chairman Roman Zhdanov … now we are the largest independent oilfield services company in Russia without any hidden liabilities. … We are Halliburton\'s successor in all obligations, including contracts.',
     'url': _HAL_IFX,
     'why': WHY + '; правопреемство покупателя по обязательствам и контрактам (интервью Интерфаксу)'},

    # ---------------- g4fb4d8b0 — Новатэк / «Тернефтегаз»
    {'id': 'g4fb4d8b0', 'field': 'src', 'old': None,
     'new': ['The National', _TTE_NAT],
     'quote': 'TotalEnergies also said it would gradually suspend activities in Russia which do not contribute to the security of energy supply of Europe.',
     'url': _TTE_NAT,
     'why': WHY + '; причина продажи по словам продавца'},
    {'id': 'g4fb4d8b0', 'field': 'src', 'old': None,
     'new': ['Yahoo Finance (Reuters)', _TTE_REU],
     'quote': 'It said all the gas condensate produced by Terneftegaz was supplied to Novatek, in which TotalEnergies also holds 19.4%',
     'url': _TTE_REU,
     'why': WHY + '; публикация Le Monde накануне подписания и ответ TotalEnergies'},
    {'id': 'g4fb4d8b0', 'field': 'src', 'old': None,
     'new': ['LNG Prime', _TTE_LNG],
     'quote': 'As a result, Novatek and TotalEnergies signed the final sale and purchase agreement on August 26, it said.',
     'url': _TTE_LNG,
     'why': WHY + '; дата окончательного договора, доля TotalEnergies в «Новатэке»'},
    {'id': 'g4fb4d8b0', 'field': 'eco.rationale',
     'old': '—',
     'new': 'TotalEnergies объясняла продажу тем, что постепенно сворачивает в России все, что не служит энергоснабжению Европы: Термокарстовое месторождение, газ которого шел на внутренний российский рынок, она законсервировала еще в первой половине 2022 года. За два дня до подписания окончательного договора Le Monde при участии Global Witness написала, что конденсат «Тернефтегаза» шел на выпуск авиатоплива, которое могли использовать российские военные. TotalEnergies ответила, что весь конденсат совместного предприятия получал «Новатэк», где у нее было 19,4%, и что продажи «Новатэка» она не контролирует.',
     'quote': 'TotalEnergies also said it would gradually suspend activities in Russia which do not contribute to the security of energy supply of Europe. … This included assets producing oil [Kharyaga field] and gas for the local Russian market [Termokarstovoye field] as well as other local businesses [lubricants, batteries] which were mothballed in the first half of the year, … Alkesh Sharma August 26, 2022 … Tassilo Hummel August 24, 2022 … TotalEnergies is involved in supplying gas condensate to make jet fuel that may have been used by Russia\'s military in Ukraine, via the French firm\'s stake in a venture with Russia\'s Novatek, Le Monde newspaper reported on Wednesday. … compiled with help from activist group Global Witness … It said all the gas condensate produced by Terneftegaz was supplied to Novatek, in which TotalEnergies also holds 19.4%, adding: "TotalEnergies has no information on, or control over, Novatek\'s independent sales to the Russian market." … As a result, Novatek and TotalEnergies signed the final sale and purchase agreement on August 26, it said.',
     'url': _TTE_REU,
     'why': WHY + '; «Цель сделки» была пустой: причина продажи и спор об авиатопливе накануне подписания'},

    # ---------------- ge0af58de — «Дело» / Global Ports
    {'id': 'ge0af58de', 'field': 'src', 'old': None,
     'new': ['A.P. Moller-Maersk', _MAERSK],
     'quote': 'With the divestment of its shares in GPI, APMT will no longer be involved in any entities operating in Russia or own any assets it the country.',
     'url': _MAERSK,
     'why': WHY + '; сообщение продавца о соглашении и причине продажи'},
    {'id': 'ge0af58de', 'field': 'src', 'old': None,
     'new': ['Прайм', _GP_PRIME],
     'quote': 'Чистая прибыль Global Ports по МСФО в 2021 году выросла в 2,9 раза по сравнению с предыдущим годом и составила 143,9 миллиона долларов, сообщает компания.',
     'url': _GP_PRIME,
     'why': WHY + '; финансы предмета за год до сделки'},
    {'id': 'ge0af58de', 'field': 'eco.rationale',
     'old': '—',
     'new': 'Maersk продавала долю, выполняя решение уйти из России: после сделки у ее терминального подразделения APM Terminals не осталось в стране ни активов, ни участия в работающих там компаниях. Покупателем стал давний партнер по Global Ports — группа «Дело», у которой было столько же акций.',
     'quote': 'Following the announcement of Maersk’s commitment to discontinue activities in Russia earlier this year, APMT has now entered into a binding agreement, subject to regulatory approvals, to divest its entire 30.75% shareholding in GPI to APMT’s long-standing joint venture partner Delo Group who also owns 30.75% of the shares in GPI. … With the divestment of its shares in GPI, APMT will no longer be involved in any entities operating in Russia or own any assets it the country.',
     'url': _MAERSK,
     'why': WHY + '; «Цель сделки» была пустой: причина продажи по сообщению Maersk'},
    {'id': 'ge0af58de', 'field': 'eco.target_fin',
     'old': '—',
     'new': 'По МСФО за 2021 год, последний перед сделкой, выручка Global Ports — 502,8 млн $, скорректированная EBITDA — 246,2 млн $, чистая прибыль — 143,9 млн $.',
     'quote': 'Чистая прибыль Global Ports по МСФО в 2021 году выросла в 2,9 раза по сравнению с предыдущим годом и составила 143,9 миллиона долларов, сообщает компания. … "Выручка выросла на 30,8% до 502,8 миллиона долларов (+17,1% на сопоставимом базисе)….Операционная прибыль выросла на 25,2%, до 197,1 миллиона долларов. … скорректированная EBITDA по итогам года выросла на 17,4%, до 246,2 миллиона долларов',
     'url': _GP_PRIME,
     'why': WHY + '; финансы предмета были пусты'},

    # ---------------- g083ec8ce — Raisio / «Копэкер Агро»
    {'id': 'g083ec8ce', 'field': 'src', 'old': None,
     'new': ['Инк.', _RAI_INC],
     'quote': 'Покупатель бизнеса, «Копэкер Агро», зарегистрирован в подмосковном Серпухове в 2016 году',
     'url': _RAI_INC,
     'why': WHY + '; русское имя покупателя, где и когда зарегистрирован, его финансы'},
    {'id': 'g083ec8ce', 'field': 'src', 'old': None,
     'new': ['Retail.ru', _RAI_RETAIL],
     'quote': 'Собственного производства в России у финской компании не было.',
     'url': _RAI_RETAIL,
     'why': WHY + '; у продавца не было своего производства в России'},
    {'id': 'g083ec8ce', 'field': 'src', 'old': None,
     'new': ['Raisio (сообщение 29 апреля 2022)', _RAI_APR],
     'quote': 'The decision was based on a rapid strategic assessment, launched immediately after Russia’s invasion of Ukraine at the end of February.',
     'url': _RAI_APR,
     'why': WHY + '; сообщение продавца о подписании и причине продажи'},
    {'id': 'g083ec8ce', 'field': 'buyer_name',
     'old': 'Copacker Agro',
     'new': 'ООО «Копэкер Агро»',
     'quote': 'Выручка ООО «Копэкер Агро», купившего российский бизнес Raisio, в 2021-м составила 64,9 млн руб.',
     'url': _RAI_INC,
     'why': WHY + '; покупатель — российское юрлицо, его имя по-русски названо в Инк.'},
    {'id': 'g083ec8ce', 'field': 'eco.rationale',
     'old': '—',
     'new': 'Решение продать российский бизнес Raisio приняла после быстрой стратегической оценки, начатой сразу после вторжения России в Украину. Гендиректор группы Пекка Куусниеми объяснял, что продолжать работу в России компания не может, а подписанные договоры позволяют уйти быстро и под контролем; по его словам, для компании и ее российских сотрудников это было лучшее решение в тех обстоятельствах.',
     'quote': 'The decision was based on a rapid strategic assessment, launched immediately after Russia’s invasion of Ukraine at the end of February. … Due to the invasion, it is not possible for us to continue our operations in Russia and the decision to sell is in line with our values. The agreements concluded will allow a rapid and controlled exit from Russia. Under the current circumstances, the solution found is the best for both the company and the employees in Russia,” says Pekka Kuusniemi, CEO of Raisio Group.',
     'url': _RAI_APR,
     'why': WHY + '; «Цель сделки» была пустой: причина продажи по сообщению продавца'},
    {'id': 'g083ec8ce', 'field': 'eco.context',
     'old': 'Финская пищевая компания Raisio вела потребительский бизнес в России через ООО «Раисио Нутришн» (каши и хлопья под маркой Nordic). Покупатель — российская компания Copacker Agro, с 12 мая 2022 года ей принадлежит 100% «Раисио Нутришн». Права на марку Nordic для России и Белоруссии отдельно купила эстонская Nordgate Trading Oü. В первом квартале 2022 года Raisio учла российский бизнес как прекращенную деятельность.',
     'new': 'Финская пищевая компания Raisio вела потребительский бизнес в России через ООО «Раисио Нутришн»: хлопья, каши, мюсли и печенье под маркой Nordic. Собственного завода в России у Raisio не было. Покупатель — ООО «Копэкер Агро», подмосковная компания по контрактному производству и упаковке продуктов, зарегистрированная в Серпухове в 2016 году; за 2021 год ее выручка составила 64,9 млн ₽, чистый убыток — 19,5 млн ₽. С 12 мая 2022 года «Копэкер Агро» принадлежит 100% «Раисио Нутришн». Права на марку Nordic для России и Белоруссии отдельно купила эстонская Nordgate Trading Oü. В первом квартале 2022 года Raisio учла российский бизнес как прекращенную деятельность.',
     'quote': '«Российские власти зарегистрировали сделку 12 мая 2022 года, бизнес дочерней компании Raisio ООО «Райсио Нутришн» передан покупателю» … Финская компания Raisio, продающая в России каши, мюсли и печенье под брендом Nordic, продала российский бизнес. Покупателем стал упаковщик продуктов питания из Подмосковья «Копэкер Агро». … Покупатель бизнеса, «Копэкер Агро», зарегистрирован в подмосковном Серпухове в 2016 году и «является одним из лидеров российского рынка контрактного производства и упаковки продуктов питания», отмечается на его сайте. … Выручка ООО «Копэкер Агро», купившего российский бизнес Raisio, в 2021-м составила 64,9 млн руб. Чистый убыток — 19,5 млн руб. … Финская компания Raisio, выпускавшая в России хлопья, каши и мюсли под маркой Nordic … Собственного производства в России у финской компании не было. … The change in the company\'s ownership has been recorded in the Unified State Register of Legal Entities, which showed that 100% of Raisio Nutrition is owned by Copacker Agro as of May 12. … In these markets, the rights to the trademark were sold to the Estonian company Nordgate Trading Oü. … Raisio Group classified the operations sold as assets held for sale in the reporting for the first quarter of 2022 and reported them as discontinued operations.',
     'url': _RAI_INC,
     'why': WHY + '; покупатель описан по Инк., у продавца не было производства в России (Retail.ru)'},
    {'id': 'g083ec8ce', 'field': 'law.struct',
     'old': 'Юрлицо купила Copacker Agro; права на марку Nordic в России и Белоруссии — эстонская Nordgate Trading Oü.',
     'new': 'ООО «Раисио Нутришн» купило ООО «Копэкер Агро»; права на марку Nordic в России и Белоруссии — эстонская Nordgate Trading Oü.',
     'quote': 'Выручка ООО «Копэкер Агро», купившего российский бизнес Raisio … бизнес дочерней компании Raisio ООО «Райсио Нутришн» передан покупателю … Права на товарный знак Nordic в России и Белоруссии купила компания из Эстонии Nordgate. … In these markets, the rights to the trademark were sold to the Estonian company Nordgate Trading Oü.',
     'url': _RAI_INC,
     'why': WHY + '; имя покупателя по-русски, как в buyer_name'},
]
