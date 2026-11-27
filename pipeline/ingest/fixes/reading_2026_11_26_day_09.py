# -*- coding: utf-8 -*-
"""Дневной обыск 26 ноября 2026, партия day_09 (REVISION_BRIEF.md, первый уровень).

Поиск источников:
  gef7d7e86 (Accenture/Axenix) — Интерфакс (англ.) 12.04.2022: доли по ЕГРЮЛ на
    11 апреля (Диланян 33%, остальные 5–17%), выручка и прибыль за 2020 год по
    СПАРК; заявление Accenture о завершении передачи; 10-K за 2022 ф. г. —
    убыток от выбытия российского бизнеса 96 млн долларов. Консультантов,
    публикации Коммерсанта о сделке не нашли.
  g5442f060 (Danfoss/«Ридан») — годовые отчеты Danfoss за 2022 и 2023 годы:
    сделка ждала одобрения российских властей, оплата считалась очень
    неопределенной, акции оценены в ноль; российские компании выведены из
    консолидации с конца августа 2022 года; в 2023 году деятельность в России
    прекращена. Закрытия сделки не нашли — статус «Подписана» не трогаем.
    Inc. Russia: чистая прибыль 2,4 млрд ₽ за 2021 год (по «Чекко»). История
    участников ООО «Ридан» (ОГРН 1035003060861) в Датаньютоне пуста.
  g2b958c12 (Stora Enso/«Сетново Групп») — полугодовой отчет Stora Enso:
    продажа лесопилок завершена, формальности по лесозаготовительным юрлицам —
    во втором полугодии 2022 года. Владельцев покупателя и согласований не нашли.
  g0ecc5666 (Otis/Ice Development) — Интерфакс (англ.) 09.09.2026: «Метеор Лифт»
    в июле 2026 года ушел к «Метеор Управляющей компании», ее 100% получил банк
    «Дом.РФ», у которого активы были в залоге. 10-K Otis за 2022 год называет
    убытки от продажи, но дословного текста получить не удалось — не записано.
  g9aaaaa3e (Hyve/Rise Expo) — TourDom 15.03.2023 (покупатель — новая компания из
    ОАЭ, контроль у гражданина Германии по данным Hyve; российское ООО
    переименовано, учредитель прежний); FashionUnited — выручка российского
    бизнеса за полугодие. Консультантов сделки (кроме PR-агентства) не нашли.
"""

WHY = 'дневной обыск 26 ноября 2026 (партия day_09)'

ACN_IFX = 'https://interfax.com/newsroom/top-stories/78109/'
ACN_10K = 'https://www.sec.gov/Archives/edgar/data/1467373/000146737322000295/acn-20220831.htm'
DAN_AR22 = 'https://assets.danfoss.com/documents/latest/403512/AH493132301547en-000101.pdf'
DAN_INC = 'https://incrussia.ru/news/danfoss-prodast-biznes/'
SE_H1 = 'https://prnewswire.co.uk/news-releases/stora-enso-oyj-half-year-report-january-june-2022-883420126.html'
OTIS_DOMRF = 'https://interfax.com/newsroom/top-stories/119051/'
HYVE_TD = 'https://www.tourdom.ru/news/turisticheskaya-vystavka-mitt-vnov-provoditsya-v-moskve-benefitsiary-vse-te-zhe-.html'
HYVE_FU = 'https://fashionunited.com/executive/report/pure-london-owner-hyve-group-to-sell-russian-business/2022040646947'

FIXES = [
    # ---------------- gef7d7e86 — Accenture / Axenix
    {'id': 'gef7d7e86', 'field': 'src', 'old': None,
     'new': ['Интерфакс', ACN_IFX],
     'quote': 'As of April 11, 33% of Accenture LLC is owned by CEO Vartan Dilanyan and other senior executives hold stakes of 5% to 17%, the Unified State Register of Legal Entities showed.',
     'url': ACN_IFX,
     'why': WHY + '; доли новых владельцев на дату сделки, финансы за 2020 год'},
    {'id': 'gef7d7e86', 'field': 'src', 'old': None,
     'new': ['Accenture (годовой отчет 10-K)', ACN_10K],
     'quote': 'During fiscal 2022, we disposed of our business in Russia and recorded a non-operating loss of $96 million.',
     'url': ACN_10K,
     'why': WHY + '; убыток продавца от выбытия российского бизнеса'},
    {'id': 'gef7d7e86', 'field': 'eco.share',
     'old': '100% доли в ООО «Аксенчер»',
     'new': '100% доли в ООО «Аксенчер»; на 11 апреля 2022 года гендиректору Вартану Диланяну принадлежало 33%, другим топ-менеджерам — от 5% до 17%.',
     'quote': 'Top Stories 12 Apr 2022 … "The new company, which will be renamed, is now 100% owned by local leadership and 100% independent from Accenture," the company said. As of April 11, 33% of Accenture LLC is owned by CEO Vartan Dilanyan and other senior executives hold stakes of 5% to 17%, the Unified State Register of Legal Entities showed.',
     'url': ACN_IFX,
     'why': WHY + '; распределение долей между покупателями на дату сделки'},
    {'id': 'gef7d7e86', 'field': 'eco.target_fin',
     'old': '—',
     'new': 'По данным системы СПАРК-Интерфакс, ООО «Аксенчер» закончило 2020 год с выручкой 8 млрд ₽ и чистой прибылью 1,75 млрд ₽.',
     'quote': 'The Russian division closed 2020 … with a net profit of 1.75 billion rubles on revenue of 8 billion rubles, the SPARK-Interfax system showed.',
     'url': ACN_IFX,
     'why': WHY + '; масштаб предмета до сделки'},
    {'id': 'gef7d7e86', 'field': 'eco.val',
     'old': '—',
     'new': 'Цена не раскрыта. Accenture отразила по выбытию российского бизнеса внеоперационный убыток в 96 млн долларов за 2022 финансовый год.',
     'quote': 'During fiscal 2022, we disposed of our business in Russia and recorded a non-operating loss of $96 million.',
     'url': ACN_10K,
     'why': WHY + '; годовой отчет продавца: убыток от выбытия'},

    # ---------------- g5442f060 — Danfoss / «Ридан»
    {'id': 'g5442f060', 'field': 'src', 'old': None,
     'new': ['Danfoss (годовой отчет за 2022 год)', DAN_AR22],
     'quote': 'Danfoss has signed an agreement to divest the shareholdings in Russia to the local management. This process is ongoing and is awaiting approval from the relevant authorities in Russia.',
     'url': DAN_AR22,
     'why': WHY + '; первоисточник продавца: сделка ждет одобрения российских властей'},
    {'id': 'g5442f060', 'field': 'src', 'old': None,
     'new': ['Inc. Russia', DAN_INC],
     'quote': 'По данным сервиса «Чекко», чистая прибыль Danfoss в России в 2021 году составила 2,4 млрд руб.',
     'url': DAN_INC,
     'why': WHY + '; финансы предмета'},
    {'id': 'g5442f060', 'field': 'law.appr',
     'old': '—',
     'new': 'Сделка ждала одобрения российских властей: в годовом отчете за 2022 год Danfoss писала, что разрешение еще не получено.',
     'quote': 'On July 15, 2022, Danfoss signed the agreement to sell its Russian businesses to the local management in Russia, currently pending local Russian approval. … This process is ongoing and is awaiting approval from the relevant authorities in Russia.',
     'url': DAN_AR22,
     'why': WHY + '; годовой отчет продавца о согласовании'},
    {'id': 'g5442f060', 'field': 'eco.val',
     'old': 'Цена не раскрыта. По сообщениям Danfoss, обесценение чистых активов в России — 85 млн евро.',
     'new': 'Цена не раскрыта. Danfoss списала российские активы с убытком около 85 млн евро; получение оплаты концерн считал очень неопределенным и оценил акции российских дочерних компаний в ноль.',
     'quote': 'This has resulted in a loss of approximately EUR 85 … which is recorded under Other Operating Expenses. Danfoss has signed an agreement to divest the shareholdings in Russia to the local management. This process is ongoing and is awaiting approval from the relevant authorities in Russia. Any consideration for the transfer is considered very uncertain and the value of the shares in the Russian subsidiaries are thus recorded to nil.',
     'url': DAN_AR22,
     'why': WHY + '; годовой отчет продавца: оплата неопределенна, акции оценены в ноль'},
    {'id': 'g5442f060', 'field': 'law.struct',
     'old': '—',
     'new': 'С конца августа 2022 года Danfoss перестала включать российские компании в свою отчетность: концерн признал, что больше не может ими управлять и выводить из них деньги.',
     'quote': 'Danfoss reassessed its ability to controls its Russian subsidiaries and determined that as of end of August 2022, it can no longer exercise control over these entities or repatriate funds. Thus, Danfoss deconsolidated its Russian activities as of August 31, 2022.',
     'url': DAN_AR22,
     'why': WHY + '; потеря контроля над российскими компаниями до закрытия сделки'},
    {'id': 'g5442f060', 'field': 'eco.target_fin',
     'old': '—',
     'new': 'Чистая прибыль российского бизнеса Danfoss за 2021 год — 2,4 млрд ₽ (по данным сервиса «Чекко»).',
     'quote': 'По данным сервиса «Чекко», чистая прибыль Danfoss в России в 2021 году составила 2,4 млрд руб.',
     'url': DAN_INC,
     'why': WHY + '; финансы предмета'},

    # ---------------- g2b958c12 — Stora Enso / «Сетново Групп»
    {'id': 'g2b958c12', 'field': 'src', 'old': None,
     'new': ['Stora Enso (отчет за первое полугодие 2022 года)', SE_H1],
     'quote': 'The divestment of the Group\'s two sawmills in Russia to local management has been completed.',
     'url': SE_H1,
     'why': WHY + '; продавец подтвердил завершение сделки'},
    {'id': 'g2b958c12', 'field': 'extra',
     'old': 'Stora Enso продала местному руководству две российские лесопилки и лесозаготовительный бизнес.',
     'new': 'Stora Enso продала местному руководству две российские лесопилки и лесозаготовительный бизнес. В отчете за первое полугодие 2022 года компания сообщила, что продажа лесопилок завершена, а оформление лесозаготовительных юрлиц ожидалось во втором полугодии.',
     'quote': 'Stora Enso Oyj Half-year Report January-June 2022 … The divestment of the Group\'s two sawmills in Russia to local management has been completed. Minor formalities for the Russian legal entities in the wood supply operations, are expected to be completed during H2/2022.',
     'url': SE_H1,
     'why': WHY + '; завершение сделки по отчету продавца'},

    # ---------------- g0ecc5666 — Otis / Ice Development
    {'id': 'g0ecc5666', 'field': 'src', 'old': None,
     'new': ['Интерфакс', OTIS_DOMRF],
     'quote': 'Meteor Management Company became the owner of Meteor Lift in July 2026, prior to which Meteor Lift was wholly owned by JSC Ice Development, part of the S8 Capital holding company',
     'url': OTIS_DOMRF,
     'why': WHY + '; дальнейшая судьба актива: переход к «Дом.РФ»'},

    # ---------------- g9aaaaa3e — Hyve / Rise Expo
    {'id': 'g9aaaaa3e', 'field': 'src', 'old': None,
     'new': ['TourDom', HYVE_TD],
     'quote': 'В июле прошлого года российское юрлицо поменяло название – ООО «Хайв Экспо Интернешнл» было переименовано в ООО «Айтии Экспо Интернешнл».',
     'url': HYVE_TD,
     'why': WHY + '; покупатель и российское юрлицо после сделки'},
    {'id': 'g9aaaaa3e', 'field': 'src', 'old': None,
     'new': ['FashionUnited', HYVE_FU],
     'quote': 'In the six months ended March 31, Hyve delivered revenue of approximately 58 million pounds, up from 5 million pounds a year earlier when it was heavily impacted by the pandemic, and excluding Russian revenues of around 17 million pounds.',
     'url': HYVE_FU,
     'why': WHY + '; выручка российского бизнеса'},
    {'id': 'g9aaaaa3e', 'field': 'law.struct',
     'old': '—',
     'new': 'Rise Expo Limited — новая компания, зарегистрированная в ОАЭ как международная коммерческая; по данным Hyve, после сделки контроль в ней должен был принадлежать гражданину Германии с большим опытом в выставочной отрасли. Российское ООО «Хайв Экспо Интернешнл» в июле того же года переименовано в ООО «Айтии Экспо Интернешнл»; учредителем, по данным сервиса проверки контрагентов, осталась британская компания «Хайв Энтерпрайзес Лимитед».',
     'quote': 'В июле прошлого года российское юрлицо поменяло название – ООО «Хайв Экспо Интернешнл» было переименовано в ООО «Айтии Экспо Интернешнл». При этом учредитель остался тот же – по данным сервиса проверки контрагентов Checko.ru, это все та же английская компания «ХАЙВ ЭНТЕРПРАЙЗЕС ЛИМИТЕД». … «Rise Expo Limited является новым юридическим лицом, зарегистрированным как международная коммерческая компания в Объединенных Арабских Эмиратах. По данным Hyve, после завершения сделки контрольный пакет акций будет принадлежать гражданину Германии со значительным опытом работы в индустрии мероприятий», – сообщал Reuters.',
     'url': HYVE_TD,
     'why': WHY + '; кто стоит за покупателем, российское юрлицо после сделки'},
    {'id': 'g9aaaaa3e', 'field': 'eco.target_fin',
     'old': '—',
     'new': 'За шесть месяцев перед объявлением о продаже (до 31 марта) российский бизнес принес около 17 млн фунтов выручки.',
     'quote': 'In the six months ended March 31, Hyve delivered revenue of approximately 58 million pounds, up from 5 million pounds a year earlier when it was heavily impacted by the pandemic, and excluding Russian revenues of around 17 million pounds.',
     'url': HYVE_FU,
     'why': WHY + '; масштаб предмета'},
]
