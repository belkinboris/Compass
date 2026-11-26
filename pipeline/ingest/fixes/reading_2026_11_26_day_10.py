# -*- coding: utf-8 -*-
"""Дневной обыск 26 ноября 2026, партия day_10 (REVISION_BRIEF.md, первый уровень).

Поиск источников:
  g88dcf73e (Kerry/Apollo Ingredients) — сайт ALLWIN (бывшее ООО «Керри»,
    теперь ООО «Олвин»): завод в Истре с 2018 года, 32 тыс. т в год, интервью
    Оливье Пикара о переходе к местному менеджменту к концу 2022 года;
    Food Business MEA — убыток группы от продажи бизнеса в России и Белоруссии
    63 млн евро. Шаг 0: предмет был описанием («российская дочерняя компания
    ирландского производителя…») — заменен именем юрлица. Владельцев Apollo,
    выручки «Олвина», консультантов не нашли (rbc companies — 401, финансов в
    Датаньютоне нет). Руководитель ООО «Олвин» по Датаньютону — «Пикар О.»,
    0,1% у Picard Investments B.V. — связь с покупателем не записана: это вывод,
    а не слова источника.
  g1e6bcc9d (Holcim/«Новая группа») — Global Cement (2 заметки), Retail.ru
    (Интерфакс 14.12.2022), поиски по владельцу «Новой группы», одобрению
    правкомиссии, финансам «Цементума», консультантам — ничего сверх известного.
  g221282a6 (Ford/«Соллерс») — Коммерсантъ 27.10.2022 (продажи Transit,
    мнение Владимира Беспалова о цене, планы «Соллерса» на завод), Reuters
    (через Yahoo) — 122 млн долларов списаны раньше, новых списаний нет;
    Интерфакс (англ.) 26.10.2022 — продажи Transit за 9 месяцев 2022 года.
    Консультантов не нашли.
  g46b308d6 (TotalEnergies/«Зарубежнефть») — Oil & Gas Journal: продажа
    завершена 3 августа 2022 года (дата). Шаг 0: law.struct в настоящем
    времени при «Закрыта»; law.terms подавал как факт то, что Коммерсантъ
    передает со слов источников (снятие инвестиционных обязательств).
  g64f192e9 (Paulig/Викас Сои) — New Retail (Финмаркет): выручка и убыток
    ООО «Паулиг Рус» за 2020 год; Retail.ru (Интерфакс): «Милфудс» за 2022 год,
    прибыльный 2021 год; Sostav (ТАСС): марку Paulig разрешили до конца
    октября 2022 года; Retail.ru («Известия»): обращение «Общественной
    потребительской инициативы» об отмене сделки — не записано (eco.context
    плотный, итог обращения неизвестен).
"""

WHY = 'дневной обыск 26 ноября 2026 (партия day_10)'

FIXES = [
    # ---------------- g88dcf73e — Kerry / Apollo Ingredients
    {'id': 'g88dcf73e', 'field': 'src', 'old': None,
     'new': ['ALLWIN', 'https://allwin-ingredients.com/en/news/olive-pikar-uznavat-adaptirovatsia-i-pobezdat'],
     'quote': "By the end of 2022, the process of Kerry's transition to local management was completed. At the beginning of 2023, the company was renamed to Olvin LLC, and a complete rebranding was carried out.",
     'url': 'https://allwin-ingredients.com/en/news/olive-pikar-uznavat-adaptirovatsia-i-pobezdat',
     'why': WHY + '; переход к местному менеджменту и новое имя компании'},
    {'id': 'g88dcf73e', 'field': 'src', 'old': None,
     'new': ['ALLWIN', 'https://allwin-ingredients.com/about'],
     'quote': 'Локальное производство было открыто в 2018 году и на сегодняшний день производит 32 000 тонн продукции в год.',
     'url': 'https://allwin-ingredients.com/about',
     'why': WHY + '; завод предмета сделки'},
    {'id': 'g88dcf73e', 'field': 'src', 'old': None,
     'new': ['Food Business MEA', 'https://www.foodbusinessmea.com/kerry-group-full-year-profits-impacted-by-exit-from-russia-and-belarus-despite-19-3-jump-in-revenues/'],
     'quote': 'This disposal cost the group a loss of €63 million',
     'url': 'https://www.foodbusinessmea.com/kerry-group-full-year-profits-impacted-by-exit-from-russia-and-belarus-despite-19-3-jump-in-revenues/',
     'why': WHY + '; убыток от продажи'},
    {'id': 'g88dcf73e', 'field': 'asset',
     'old': 'Российская дочерняя компания ирландского производителя пищевых ингредиентов',
     'new': 'ООО «Олвин»',
     'quote': 'ООО "ОЛВИН" Производство прочих продуктов питания, не включенных в другие группировки location_on МОСКОВСКАЯ person Пикар О. ИНН: 7707597514',
     'url': 'https://datanewton.ru/search?query=7707597514',
     'why': WHY + '; шаг 0: в предмете стояло описание вместо имени юрлица'},
    {'id': 'g88dcf73e', 'field': 'eco.share',
     'old': '100% ООО «Керри»',
     'new': '100% ООО «Керри» (теперь «Олвин», бренд ALLWIN) — завод вкусоароматических ингредиентов в Истре, открытый в 2018 году (32 000 т продукции в год), и центр разработок в Подмосковье',
     'quote': 'It also agreed a deal to divest 100% of the share capital of Kerry Limited Liability Company, its subsidiary in Russia, to local management. … At the beginning of 2023, the company was renamed to Olvin LLC … Компания ALLWIN предлагает вкусоароматические и функциональные решения … 2018 Открытие завода в Истре Локальное производство было открыто в 2018 году и на сегодняшний день производит 32 000 тонн продукции в год. … We were the first to open a research and development center in the Moscow region in 2014.',
     'url': 'https://allwin-ingredients.com/about',
     'why': WHY + '; что именно перешло покупателю'},
    {'id': 'g88dcf73e', 'field': 'eco.val',
     'old': 'Цена не раскрыта. В первом полугодии 2022 года Kerry списала около 38 млн евро, обнулив стоимость активов в России и Белоруссии.',
     'new': 'Цена не раскрыта. В первом полугодии 2022 года Kerry списала около 38 млн евро, обнулив стоимость активов в России и Белоруссии. Убыток группы от продажи бизнеса в обеих странах — 63 млн евро.',
     'quote': 'Kerry Group ranks second, having absorbed an almost €38 million impairment charge in the first half of last year reducing the value of its assets in Russia and Belarus to nil. … By the end of 2022, the process of Kerry\'s transition to local management was completed. … It reached an agreement to sell its taste and nutrition entity in Belarus and divested 100% of share capital of its Russian subsidiary to local management. This disposal cost the group a loss of €63',
     'url': 'https://www.foodbusinessmea.com/kerry-group-full-year-profits-impacted-by-exit-from-russia-and-belarus-despite-19-3-jump-in-revenues/',
     'why': WHY + '; убыток от продажи'},

    # ---------------- g221282a6 — Ford / «Соллерс»
    {'id': 'g221282a6', 'field': 'src', 'old': None,
     'new': ['Коммерсантъ', 'https://www.kommersant.ru/doc/5634185'],
     'quote': 'Ford Motor Company объявила, что финализировала сделку по выходу из российского СП «Соллерс Форд».',
     'url': 'https://www.kommersant.ru/doc/5634185',
     'why': WHY + '; продажи Transit, оценка эксперта, планы покупателя'},
    {'id': 'g221282a6', 'field': 'src', 'old': None,
     'new': ['Reuters (Yahoo Finance)', 'https://uk.finance.yahoo.com/news/ford-exit-russia-jv-stake-141033178.html'],
     'quote': 'The U.S. automaker took a $122 million writedown connected to its suspension of Russian operations earlier this year but will not take additional writedowns',
     'url': 'https://uk.finance.yahoo.com/news/ford-exit-russia-jv-stake-141033178.html',
     'why': WHY + '; списания Ford'},
    {'id': 'g221282a6', 'field': 'src', 'old': None,
     'new': ['Интерфакс', 'https://interfax.com/newsroom/top-stories/84331/'],
     'quote': 'In the first nine months of 2022, sales of Ford Transits in Russia tumbled by 61.5% to 5,394 vehicles',
     'url': 'https://interfax.com/newsroom/top-stories/84331/',
     'why': WHY + '; продажи Transit в 2022 году'},
    {'id': 'g221282a6', 'field': 'eco.val',
     'old': 'Ford продала долю по номиналу; денежная сумма в статьях не названа.',
     'new': 'Ford продала долю по номиналу; денежная сумма в статьях не названа. Новых списаний из-за продажи компания не делала: 122 млн долларов она списала раньше, когда остановила работу в России. Автомобильный эксперт Владимир Беспалов считал маловероятным, что долю, как в 2019 году, оценили в сотни миллионов долларов: завод стоял, перспективы были неясны, а опцион на обратный выкуп обычно снижает цену.',
     'quote': 'Ford at the end of October announced its decision to sell the 49% non-controlling stake in the Russian JV at par value. … The U.S. automaker took a $122 million writedown connected to its suspension of Russian operations earlier this year but will not take additional writedowns in connection with Wednesday\'s announcement … Автомобильный эксперт Владимир Беспалов считает низкой вероятность того, что доля оценивается, как в 2019 году, в сотни миллионов долларов с учетом остановки завода и неясных перспектив возобновления. … Кроме того, отмечает он, опцион, как правило, снижает цену.',
     'url': 'https://www.kommersant.ru/doc/5634185',
     'why': WHY + '; списания продавца и оценка эксперта'},
    {'id': 'g221282a6', 'field': 'eco.target_fin',
     'old': '—',
     'new': 'С середины 2019 года СП выпускало в Елабуге только Ford Transit. В 2021 году в России продали 20,8 тыс. таких машин, на 48% больше, чем годом раньше; за девять месяцев 2022 года продажи упали на 61,5%. С 3 марта 2022 года завод простаивал.',
     'quote': 'The Ford Sollers joint venture had been producing only Ford Transit LCVs in various modifications at a plant in Yelabuga, Tatarstan since the middle of 2019 … В 2021 году продажи Ford Transit в России выросли на 48%, до 20,8 тыс. машин. … In the first nine months of 2022, sales of Ford Transits in Russia tumbled by 61.5% to 5,394 vehicles … The joint venture in Yelabuga went idle on March 3.',
     'url': 'https://interfax.com/newsroom/top-stories/84331/',
     'why': WHY + '; масштаб бизнеса СП'},
    {'id': 'g221282a6', 'field': 'eco.rationale',
     'old': '—',
     'new': '«Соллерс» заранее объявил, что загрузит бывшее производство Ford Transit в Елабуге легкими коммерческими машинами собственной марки на платформе китайского партнера; первые товарные машины обещал выпустить в конце 2022 года.',
     'quote': '«Соллерс» уже анонсировал, что в конце 2022 года выпустит первые товарные автомобили под своей маркой на базе бывшего производства Ford Transit. Новая линейка LCV создается на платформе китайского партнера',
     'url': 'https://www.kommersant.ru/doc/5634185',
     'why': WHY + '; что покупатель делает с заводом'},

    # ---------------- g46b308d6 — TotalEnergies / «Зарубежнефть»
    {'id': 'g46b308d6', 'field': 'src', 'old': None,
     'new': ['Oil & Gas Journal', 'https://www.ogj.com/general-interest/companies/article/14281846/totalenergies-to-divest-termokarstovoye-gas-field-interest-to-novatek'],
     'quote': 'The company finalized the sale of its remaining 20% interest in Kharyaga to state-controlled operator Zarubezhneft on Aug. 3, 2022.',
     'url': 'https://www.ogj.com/general-interest/companies/article/14281846/totalenergies-to-divest-termokarstovoye-gas-field-interest-to-novatek',
     'why': WHY + '; дата завершения'},
    {'id': 'g46b308d6', 'field': 'law.struct',
     'old': 'Доля передается в рамках соглашения о разделе продукции; для этого к соглашению подписывается дополнение.',
     'new': 'Долю передавали внутри соглашения о разделе продукции: правительство поручило министру энергетики Николаю Шульгинову подписать к нему дополнение. TotalEnergies завершила продажу 3 августа 2022 года.',
     'quote': 'A corresponding instruction to sign an addendum to the PSA was given to Energy Minister Nikolai Shulginov. … The company finalized the sale of its remaining 20% interest in Kharyaga to state-controlled operator Zarubezhneft on Aug. 3, 2022.',
     'url': 'https://www.ogj.com/general-interest/companies/article/14281846/totalenergies-to-divest-termokarstovoye-gas-field-interest-to-novatek',
     'why': WHY + '; шаг 0: настоящее время при «Закрыта»'},
    {'id': 'g46b308d6', 'field': 'law.terms',
     'old': 'Вместе с долей с TotalEnergies снимаются инвестиционные обязательства по проекту.',
     'new': 'По неофициальным данным, вместе с долей у TotalEnergies должны были прекратиться обязательства инвестировать в проект.',
     'quote': 'По словам одного из собеседников “Ъ”, сделка между Total и «Зарубежнефтью» может быть безденежной, при этом у Total прекратятся обязательства по инвестированию в актив.',
     'url': 'https://kommersant.ru/doc/5448063',
     'why': WHY + '; шаг 0: слова источников издания были поданы как факт'},

    # ---------------- g64f192e9 — Paulig / Викас Сои
    {'id': 'g64f192e9', 'field': 'src', 'old': None,
     'new': ['New Retail', 'https://new-retail.ru/novosti/retail/godovoy_chistyy_ubytok_paulig_v_rf_sostavil_2_5_mln_rubley2256/'],
     'quote': 'По итогам 2020 года чистый убыток ООО «Паулиг Рус» (кофеобжарочный завод финской Paulig в Тверской области) составил 2,5 млн рублей против 23,1 млн рублей чистой прибыли в 2019 году.',
     'url': 'https://new-retail.ru/novosti/retail/godovoy_chistyy_ubytok_paulig_v_rf_sostavil_2_5_mln_rubley2256/',
     'why': WHY + '; финансы предмета до сделки'},
    {'id': 'g64f192e9', 'field': 'src', 'old': None,
     'new': ['Retail.ru', 'https://www.retail.ru/news/vyruchka-rossiyskoy-eks-dochki-paulig-snizilas-na-16-v-2023-godu-9-aprelya-2024-239642/'],
     'quote': '2023 год компания завершила с чистым убытком в 339,3 млн рублей, в 2022 году была получена чистая прибыль в размере 368,7 млн рублей.',
     'url': 'https://www.retail.ru/news/vyruchka-rossiyskoy-eks-dochki-paulig-snizilas-na-16-v-2023-godu-9-aprelya-2024-239642/',
     'why': WHY + '; финансы предмета после сделки'},
    {'id': 'g64f192e9', 'field': 'src', 'old': None,
     'new': ['Sostav', 'https://www.sostav.ru/publication/paulig-budet-vypuskat-kofe-marki-poetti-54971.html'],
     'quote': 'По словам директора по маркетингу ООО «Милфудс» (управляет Paulig), владелец бренда разрешил его использование в России до конца октября.',
     'url': 'https://www.sostav.ru/publication/paulig-budet-vypuskat-kofe-marki-poetti-54971.html',
     'why': WHY + '; срок использования марки'},
    {'id': 'g64f192e9', 'field': 'eco.target_fin',
     'old': '—',
     'new': 'В 2020 году выручка ООО «Паулиг Рус» составила 4,46 млрд ₽, чистый убыток — 2,5 млн ₽ (в 2019 году — 23,1 млн ₽ чистой прибыли); 2021 год компания закончила с прибылью. В 2022 году, уже как «Милфудс», она получила 4,3 млрд ₽ выручки и 368,7 млн ₽ чистой прибыли.',
     'quote': 'По итогам 2020 года чистый убыток ООО «Паулиг Рус» (кофеобжарочный завод финской Paulig в Тверской области) составил 2,5 млн рублей против 23,1 млн рублей чистой прибыли в 2019 году. … Выручка компании увеличилась, но темпы роста существенно замедлились (составив 0,9%) до 4,46 млрд рублей с 4,419 млрд рублей в 2019 году. … Компания «Милфудс» (бывшая «дочка» ушедшей из РФ финской Paulig, развивает бренд Poetti) в 2023 году получила выручку в размере 3,6 млрд рублей, что на 16,3% меньше, чем в 2022 году (4,3 млрд рублей) … в 2022 году была получена чистая прибыль в размере 368,7 млн рублей. Прибыльным был и 2021 год',
     'url': 'https://www.retail.ru/news/vyruchka-rossiyskoy-eks-dochki-paulig-snizilas-na-16-v-2023-godu-9-aprelya-2024-239642/',
     'why': WHY + '; финансы предмета'},
    {'id': 'g64f192e9', 'field': 'law.terms',
     'old': 'Бренды и рецептуры Paulig остались у продавца; переходные поставки сырья — до трех месяцев.',
     'new': 'Бренды и рецептуры Paulig остались у продавца, но выпускать кофе под маркой Paulig новому владельцу разрешили до конца октября 2022 года; переходные поставки сырья — до трех месяцев.',
     'quote': 'В течение лета производитель продолжит выпускать кофе под брендом Paulig согласно договоренностями с финской компанией. По словам директора по маркетингу ООО «Милфудс» (управляет Paulig), владелец бренда разрешил его использование в России до конца октября. … 17.06.2022 … Торговые марки и рецептура в сделку не включены … в течение переходного периода, который займет не более трех месяцев',
     'url': 'https://www.sostav.ru/publication/paulig-budet-vypuskat-kofe-marki-poetti-54971.html',
     'why': WHY + '; срок использования марки Paulig'},
]
