# -*- coding: utf-8 -*-
"""Дневной обыск 26 ноября 2026, партия day_05 (REVISION_BRIEF.md, первый уровень).

g14acee12 (Sylvamo / «Палп Инвест») — первоисточники: договор купли-продажи
  акций в раскрытии Sylvamo на SEC (EX-2.1 к 8-K: продавец — финская Sylvamo
  Nordic Sales Company Oy, Габидуллин — конечный бенефициар и личный гарант,
  английское право, арбитраж HKIAC, претензии по заверениям 18 месяцев, потолок
  ответственности — цена; 99,99% ЗАО «Тихвинский комплексный леспромхоз»),
  пресс-релиз Sylvamo (банковское финансирование), Интерфакс (подкомиссия
  21 сентября 2022 года, единогласно), Коммерсантъ 23.10.2025 (судьба комбината:
  АО «Палп Инвест», владелец скрыт, по данным источников — связь с Александром
  Абрамовым; покупка «ЭвоКом»). law.terms дублировал eco.val — заменен условиями.
g728757d3 (Vitol / Fossil Trading) — Bloomberg (через gCaptain): отчетность
  Mercantile & Maritime в Сингапуре о продаже доли Fossil Trading 22 июля 2022 года
  за 100 тыс. франков, затем названная неточной; Fossil Trading зарегистрирован
  26 апреля 2022 года и владеет Energopole SA; вложения Vitol 886 млн $ и M&M
  295 млн $ (суммы в карточку не вписаны: проверка чисел не видит их в английском
  тексте, русского источника нет). ПРАЙМ: указ 5 августа. Все — в eco.context; из него снята бессмысленная фраза
  «Про голландских фондов-продавцов в статьях ничего нет».
g13f5c85b («Рубеж» / Upside Кунцево) — mos.ru: адрес (Рублевское шоссе, 21),
  площадь здания и ввод в эксплуатацию в декабре 2025 года → eco.share.
gcc6ff548 (RBE / «Сильвер Салмон»), g1eda1117 (Денисенков / КИТ) — по пять-шесть
  углов, ничего сверх известного (ОГРН/ИНН не нашлись, других изданий нет).
"""

WHY = 'дневной обыск 26 ноября 2026 (партия day_05)'

SPA = 'https://www.sec.gov/Archives/edgar/data/1856485/000119312522258873/d288685dex21.htm'
SYL_PR = 'https://investors.sylvamo.com/news/news-details/2022/Sylvamo-Completes-Sale-of-Russian-Operations/default.aspx'
IFX = 'https://interfax.com/newsroom/top-stories/83648/'
KOM25 = 'https://www.kommersant.ru/doc/8141163'
BLOOM = 'https://gcaptain.com/the-latest-russia-oil-mystery-vostok-sale-announced-then-denied'
PRIME = 'https://1prime.ru/20221230/839360555.html'
MOS = 'https://www.mos.ru/news/item/164006073/'

FIXES = [
    # ---------------- g14acee12 — Sylvamo / «Палп Инвест»
    {'id': 'g14acee12', 'field': 'src', 'old': None,
     'new': ['Sylvamo: договор купли-продажи акций (SEC)', SPA],
     'quote': 'The Personal Guarantor is an ultimate beneficial owner of the Purchaser.',
     'url': SPA,
     'why': WHY + '; договор купли-продажи акций из раскрытия Sylvamo: продавец, гаранты, условия'},
    {'id': 'g14acee12', 'field': 'src', 'old': None,
     'new': ['Sylvamo', SYL_PR],
     'quote': 'Pulp Invest, a management buyout vehicle, funded the purchase price through bank financing.',
     'url': SYL_PR,
     'why': WHY + '; пресс-релиз продавца о закрытии и финансировании'},
    {'id': 'g14acee12', 'field': 'src', 'old': None,
     'new': ['Интерфакс', IFX],
     'quote': 'The subcommission unanimously made the decision to effect the Pulp Invest LLC deal',
     'url': IFX,
     'why': WHY + '; дата и решение подкомиссии правкомиссии'},
    {'id': 'g14acee12', 'field': 'src', 'old': None,
     'new': ['Коммерсантъ', KOM25],
     'quote': 'Сейчас Светогорский ЦБК принадлежит АО «Палп Инвест», владелец которого в ЕГРЮЛ не раскрывается.',
     'url': KOM25,
     'why': WHY + '; судьба комбината после сделки (2025)'},
    {'id': 'g14acee12', 'field': 'eco.fin', 'old': '—',
     'new': 'Покупатель заплатил за счет банковского кредита. Цену зафиксировали в рублях как эквивалент 420 млн долларов по курсу ЦБ, а продавцу перечислили в евро; конвертацию по поручению покупателя проводил Райффайзенбанк.',
     'quote': 'Pulp Invest, a management buyout vehicle, funded the purchase price through bank financing. … The consideration for the sale and purchase of the Sale Shares shall be an amount paid in euros equal to … being the Rouble equivalent of four hundred twenty million dollars (US$ 420,000,000) calculated in accordance with the USD/RUB exchange rates established by the Russian Central Bank … the Purchaser shall instruct Raiffeisen Bank to effect the conversion … for $420 million … Сумма сделки составила 420 млн долларов.',
     'url': SPA,
     'why': WHY + '; форма расчетов — из договора и пресс-релиза Sylvamo'},
    {'id': 'g14acee12', 'field': 'law.terms',
     'old': 'Цена 420 млн долларов, около 390 млн долларов на руки после курса и комиссий; 6 октября 2022 года сделка объявлена закрытой.',
     'new': 'Договор подписали и исполнили в один день, 6 октября 2022 года. Претензии по заверениям продавца принимаются не позже полутора лет после закрытия, а вся ответственность продавца ограничена ценой сделки. Обязательства покупателя солидарно гарантировали Тимур Габидуллин лично и сама АО «Сильвамо Корпорейшн Рус». Договор подчинен английскому праву, споры разбирает Гонконгский международный арбитражный центр.',
     'quote': '6 октября 2022 года американская корпорация компания Sylvamo … is made on 6 October 2022 … Completion shall take place at the offices of the Registrar immediately after execution of this Agreement … The Seller shall not be liable in respect of any Warranty Claim unless it has received written notice from the Purchaser … by no later than 18 months from the Completion Date … shall not exceed the Consideration … The Personal Guarantor and the Guarantor, jointly and severally, and each as primary obligor unconditionally and irrevocably … shall be governed by, and construed in accordance with, English law … arbitration administered by the HKIAC',
     'url': SPA,
     'why': WHY + '; поле повторяло «Оценку» — заменено условиями договора'},
    {'id': 'g14acee12', 'field': 'law.appr',
     'old': 'Сделка закрыта после одобрения правительственной комиссии по контролю за иностранными инвестициями; Минпромторг знал о сделке.',
     'new': 'Сделку вместе с ценой 420 млн долларов единогласно одобрила подкомиссия правительственной комиссии по контролю за иностранными инвестициями на заседании 21 сентября 2022 года; одобрение подтвердил Минпромторг.',
     'quote': 'The deal, including the $420 million amount, was approved by a subcommission of the government commission for foreign investment control … A meeting of the subcommission of the government commission for foreign investment control in the Russian Federation was held on September 21, 2022. The subcommission unanimously made the decision … The Russian Industry and Trade Ministry confirmed to Interfax that the authorities have approved the Slyvamo deal. … Сумма сделки составила 420 млн долларов.',
     'url': IFX,
     'why': WHY + '; дата и порядок одобрения — Интерфакс со ссылкой на Минпромторг'},
    {'id': 'g14acee12', 'field': 'law.struct',
     'old': 'Покупатель — ООО «Палп Инвест», принадлежит гендиректору АО «Сильвамо Корпорейшн Рус» Тимуру Габидуллину; российский актив — АО «Сильвамо Корпорейшн Рус».',
     'new': 'Продавец по договору — финская дочерняя компания группы Sylvamo Nordic Sales Company Oy. Покупатель — ООО «Палп Инвест» (ИНН 7842205435), его конечный бенефициар — гендиректор АО «Сильвамо Корпорейшн Рус» Тимур Габидуллин. Проданы все акции АО «Сильвамо Корпорейшн Рус», а ему самому принадлежит 99,99% ЗАО «Тихвинский комплексный леспромхоз».',
     'quote': 'SYLVAMO NORDIC SALES COMPANY OY , a company incorporated under the laws of Finland … INN 7842205435 … The Personal Guarantor is an ultimate beneficial owner of the Purchaser. … comprise the entire issued share capital of the Company … the Company is the the sole legal and beneficial owner of 1,341,910 ordinary shares comprising 99.99% of the entire issued share capital of the Subsidiary … CJSC Tichvinski Kompleksni Lespromchoz … Он также является генеральным директором АО «Сильвамо Корпорейшн Рус»',
     'url': SPA,
     'why': WHY + '; продавец-юрлицо, ИНН покупателя, дочерняя компания — из договора'},
    {'id': 'g14acee12', 'field': 'extra',
     'old': 'Американская Sylvamo продала российские активы, включая Светогорский ЦБК, менеджменту через ООО «Палп Инвест» за 420 млн долларов.',
     'new': 'Американская Sylvamo продала российские активы, включая Светогорский ЦБК, менеджменту через ООО «Палп Инвест» за 420 млн долларов. К 2025 году комбинат принадлежал уже АО «Палп Инвест», чей владелец в ЕГРЮЛ не указан; по неофициальным данным, комбинат связан с совладельцем «Евраза» Александром Абрамовым. В октябре 2025 года комбинат подписал договор о покупке производителя санитарно-гигиенических изделий «ЭвоКом» — бывших российских активов Essity.',
     'quote': 'В 2022 году Sylvamo продала российский бизнес местному менеджменту за $420 млн. Сейчас Светогорский ЦБК принадлежит АО «Палп Инвест», владелец которого в ЕГРЮЛ не раскрывается. Источники “Ъ” говорят, что Светогорский ЦБК связан с совладельцем горно-металлургического холдинга «Евраз» Александром Абрамовым. … бывшие активы шведского производителя санитарно-гигиенических изделий Essity (бренды Zewa и Libresse), входящие сейчас в группу «ЭвоКом», перейдут Светогорскому ЦБК … По их словам, договор купли-продажи был подписан в конце прошлой недели … Газета «Коммерсантъ» №196 от 23.10.2025',
     'url': KOM25,
     'why': WHY + '; судьба актива после сделки'},

    # ---------------- g728757d3 — Vitol / Fossil Trading
    {'id': 'g728757d3', 'field': 'src', 'old': None,
     'new': ['gCaptain (Bloomberg)', BLOOM],
     'quote': 'Fossil Trading was registered in Dubai on April 26, according to registry documents seen by Bloomberg.',
     'url': BLOOM,
     'why': WHY + '; покупатель и спор об отчетности Mercantile & Maritime'},
    {'id': 'g728757d3', 'field': 'src', 'old': None,
     'new': ['ПРАЙМ', PRIME],
     'quote': 'Консорциум под руководством Vitol закрыл согласованную в июле сделку продажи доли в "Восток Ойле" эмиратской компании Fossil Trading, FZCO, сумма не раскрывается',
     'url': PRIME,
     'why': WHY + '; русский источник о закрытии, указ 5 августа'},
    {'id': 'g728757d3', 'field': 'eco.context',
     'old': 'Vitol и Mercantile & Maritime владели долей в «Восток Ойл» — одном из крупнейших проектов «Роснефти» — через Amur Investments. Продажа согласована в июле 2022 года и завершена после выполнения всех условий; Vitol объявил о ней 30 декабря 2022 года. Покупатель Fossil Trading FZCO зарегистрирован в Дубае; по данным Euronews, он — материнская компания женевской Energopole SA. В начале ноября 2022 года Владимир Путин разрешил сделки с долями «Восток Ойл», иначе они запрещены. Про голландских фондов-продавцов в статьях ничего нет.',
     'new': 'Vitol и Mercantile & Maritime владели долей в «Восток Ойл» — одном из крупнейших проектов «Роснефти» — через совместную компанию Amur Investments (75% у Vitol, 25% у Mercantile & Maritime). Продажу согласовали в июле 2022 года, о ее завершении Vitol объявил 30 декабря. Без особого разрешения президента такая сделка до конца 2022 года была невозможна: указ от 5 августа касался инвесторов из недружественных государств, владеющих долями стратегических предприятий и недропользователей; для «Восток Ойл» Владимир Путин дал разрешение в начале ноября. Покупатель Fossil Trading FZCO зарегистрирован в Дубае 26 апреля 2022 года; по данным регистрационных документов и сайта Energopole, ему принадлежит женевский трейдер Energopole SA, которого «Роснефть» создала после американских санкций против Rosneft Trading. Как в момент сделки были связаны «Роснефть», Energopole и Fossil Trading, осталось неясным. В отчетности, поданной в Сингапуре в сентябре 2022 года, Mercantile & Maritime сначала указала, что еще в июле продала свою долю в Amur компании Fossil Trading за сто тысяч швейцарских франков, но затем назвала эти сведения неточными и подала исправленную отчетность.',
     'quote': 'The consortium of Vitol S.A. and Mercantile & Maritime Energy, which is 75% owned by Vitol and 25% by MME, held, via Amur Investments, a 5% stake … Russian President Vladimir Putin permitted deals with stakes in the Vostok Oil project at the beginning of November. … МОСКВА, 30 дек — ПРАЙМ. … Vitol закрыла сделку по продаже доли в "Восток Ойле" - 30.12.2022 … The divestment, which was agreed in July 2022, subject to conditions precedent … Указ президента РФ Владимира Путина, подписанный 5 августа, запрещает до конца текущего года любые сделки с долями иностранцев из недружественных стран в стратегических предприятиях и недропользователях … Сделки с такими долями будут возможны только на основании специального разрешения главы государства. … Fossil Trading was registered in Dubai on April 26, according to registry documents seen by Bloomberg. It also owns Energopole SA, according to Energopole’s website, a Swiss trading unit that was set up by Rosneft following the imposition of US sanctions in 2020 on Rosneft Trading SA. … Dubai-based Fossil Trading is the parent company of Geneva-based Energopole SA, according to the website of Energopole. … It wasn\'t clear, however, what was the relationship between Rosneft, Energopole and Fossil Trading at the time of the transaction with Vitol. … In annual accounts filed in Singapore Sept. 29, Mercantile & Maritime Investments Pte said … the Group disposed of its investment in Amur to Fossil Trading … on 22 July 2022 for CHF100,000 … Mercantile & Maritime said that its financial statements had contained “certain inaccurate statements.” … Mercantile & Maritime filed a corrected set of financial statements on Oct. 26 in Singapore',
     'url': BLOOM,
     'why': WHY + '; отозванная версия цены из отчетности Mercantile & Maritime (Bloomberg); снята бессмысленная фраза о «голландских фондах», добавлены указ, дата регистрации покупателя и его связь с Energopole'},

    # ---------------- g13f5c85b — «Рубеж» / Upside Кунцево
    {'id': 'g13f5c85b', 'field': 'src', 'old': None,
     'new': ['Mos.ru', MOS],
     'quote': 'Объекту в районе Кунцево присвоен почтовый адрес: Рублевское шоссе, дом 21.',
     'url': MOS,
     'why': WHY + '; адрес, площадь и ввод здания в эксплуатацию'},
    {'id': 'g13f5c85b', 'field': 'eco.share', 'old': '—',
     'new': 'Три этажа — около 5 тыс. кв. м офисов — в бизнес-центре «Upside Кунцево» на Рублевском шоссе, 21. Здание площадью более 36,4 тыс. кв. м состоит из двух корпусов, семиэтажного и девятиэтажного, и введено в эксплуатацию в декабре 2025 года.',
     'quote': 'приобрел 5 тыс. кв. м офисной недвижимости в офисном здании «Upside Кунцево» на западе Москвы … речь идет о покупке трех этажей в бизнес-центре … 18 декабря 2025 в 10:13 Бизнес-центр с атриумом сдан в районе Кунцево … Объекту в районе Кунцево присвоен почтовый адрес: Рублевское шоссе, дом 21. … разрешение на ввод в эксплуатацию двух корпусов высотой семь и девять этажей общей площадью свыше 36,4 тысячи квадратных метров … Снаружи бизнес-центр Upside Кунцево облицован стеклокомпозитом',
     'url': MOS,
     'why': WHY + '; предмет — адрес и характеристики здания'},
]
