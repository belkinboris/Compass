# -*- coding: utf-8 -*-
"""Вычитка базы, марафон 12 ноября 2026, партия m002: двенадцать карточек против статей и реестра.

gfa14411d (LPP / Far East Services), g55f1c662 (Valio / «Дэнир»), g57b3b93c (Mayr-Melnhof / «Гранель»),
g1059432d (Whirlpool / Arçelik), gfc7e5649 (SoftwareONE Russia), gc677124b (Aggreko / «БурСервис»),
g94683ed2 («Рив Гош» / Wildberries & Russ), ga0a49202 («Клаустрофобия»), gd88cbe9a («Гейзер Голд» / Highland Gold),
g15f35a5d («Западная» / ОКТО), gbc0b68bd («Фэшн фэктори» / «Воентекстильпром»), g181d7687 («КБ Борей» / Yadro).

Каждый источник открыт заново (curl с обычным браузерным User-Agent; SEC — по правилам сайта, без личных
данных) и сохранен save_source.save() в data/inbox/triage/sources_2026-11-12_m002.json; история участников
ЕГРЮЛ (projectcompass.ru/api/companies/<id>/fns) сохранена туда же текстом. Правки — одной разовой частью:
факты (стороны, дата, сумма, доля, заголовок, консультанты) — с fact_edit_guard.log и цитатой, проза — со
сверкой prose_gate.prose_problems по цитате в сухом прогоне. Прежние записи таблицы правок на тронутые поля
гасятся отпечатком в proofread_absorbed (иначе они считались бы непримененными).

Поиск и сверка:
  gfa14411d — Ъ 5446520 (ЕГРЮЛ 30 июня 2022: 95% «РЕ Трэйдинг» у «Фар ист сервисиз-фзко», 5% у Анны Пилюгиной),
              Ъ 5652618, Leave Russia, Hindenburg Research (две части цены: $135 млн магазины + $247 млн запасы,
              опцион до конца 2026), Notes from Poland (штраф KNF 1,8 млн злотых), Omnichannel News, PDF Пепеляев
              Групп (консультант ООО «РЕ Трэйдинг», а не продавца). Продавец «ООО «РЕ Трэйдинг», LPP SA» → LPP SA
              (РЕ Трэйдинг — предмет). Дата 23 мая → 30 июня 2022 (реестр). «Интерфакс» — голый домен, статьи
              поиском не нашли — снят. Следствие прокуратуры «приостановлено до середины 2026» — ни в одном
              источнике — снято. Цель была копией «Дополнительно» — заменена мотивом из статьи.
  g55f1c662 — Retail.ru (ЕГРЮЛ 29 декабря 2022: ООО «Виола» → ООО «Дэнир»), Castren & Snellman (сделка весной
              2022; продажи в РФ 2020 — €87 млн, в карточке было 85), Интерфакс 1018641, TAdviser, Leave Russia,
              реестр (продавец в реестре — Rushold M Oy). Дата 2022-06-01 → 2022-12-29. «Русагро» и «ООО «Валио»
              заявило, что продолжит работу» — ни в одном источнике, сняты. Профили-близнецы g54913880 «Viola (бренд
              Valio в России)» и gb65d135e «ООО «Виола»» (другая карточка) — не слиты, в отчете.
  g57b3b93c — пресс-релиз MM 16.12.2022 и CMS (продажа закрыта после одобрения властей, ~€134 млн, выручка 2021 —
              ~€124 млн), Фонтанка (Ъ): «ММПОФ Пэкэджинг» и «ММПОФ Ротогравюр» — 99,99% у MM Packaging GmbH; «Невские
              грани» принадлежали Tannpapier, а не Mayr-Melnhof (этап «Свезы» это смешивал), март 2023 — ООО
              «Форвард», 27.12.2024 — «Свеза». AK&M, ПЛН, Printindustry (не открылся). Дата 1 декабря → 16 декабря.
  g1059432d — Whirlpool 10-Q за III кв. 2022 (подписание 27.06.2022, закрытие 31.08.2022, цена — условное
              вознаграждение с потолком по чистым активам €220 млн) и за III кв. 2023 (потолок уточнен — €261 млн),
              Better Chance, Retail.ru (ЕГРЮЛ 7 и 16 сентября), New Retail (финансы 2021), Daily Sabah (Reuters, июнь 2026: последний
              платеж €40 млн по всем обязательствам), TAdviser, Абирег. Сумма «€220 млн» — предел, а не цена →
              «Не раскрыта»; «общая сумма выплат ~€157 млн (117+40)» — наш неверный расчет, снят. Bloomberg — голый
              домен, снят.
  gfc7e5649 — ComNews (купили совладельцы Awara IT Александр Ермаков и Юрий Шумаков, 60/40), реестр (19 мая 2022
              СофтвэрУАН АГ вышла, вошли Ермаков и Шумаков), TAdviser, Leave Russia. Покупатель «Awara IT Group» (ООО
              «Ван Ай Ти Солюшенс») в реестре предмета не появлялся → люди по именам. «Консультант: не раскрывались» —
              заглушка в «Команде сделки», снята.
  gc677124b — пресс-релиз «БурСервиса» 20.11.2025, реестр (19 ноября 2025), распоряжение № 196-рп, Интерфакс,
              International Rental News ($29 млн — Россия $21 млн + Казахстан $8 млн), Leave Russia, AK&M, Ъ 8442557
              (о другой сделке — «Уфабурмаш»; факты о ней из контекста сняты).
  g94683ed2 — Интерфакс, Ъ 8077406 и 8292342, Malls.ru, пресс-релиз ДГП, реестр (продавец — Rive Gauche Group
              (Cyprus) Ltd, не «акционеры»). Сумма — «5–6 млрд ₽ (по оценке)» (Ъ, Бурмистров).
  ga0a49202 — РБК 15.08.2025 и 27.08.2024, Ъ 7971462, Sostav, БГ; Inc. не открылся. Покупатель — новые ООО
              «Клаустрофобия Офлайн/Онлайн» (Змовик 51%, Вараксин 33%, Авин 16%); профиль GrimTeam — ООО «Гримтим»
              Альбины Воронковой, стороной не был. Дата 1 июля → 1 августа (передача активов). 400 млн ₽ — оценка.
  gd88cbe9a — Ъ 7796300, «Золото и технологии», EastRussia, реестр (3 июня 2025 «Гиперспэйс» → МКАО «Ареал»).
              «Продавец — Андрей Комаров» неверно (продавец — ООО «Гиперспэйс»); цель «Highland Gold хочет усилить
              позиции…» — без автора (компания от комментариев отказалась) → мнение эксперта с именем.
  g15f35a5d — РБК (закрыта 25 апреля 2025, ФАС), «Золото и технологии» (×2), Абирег, LEVEL Legal Services, BIRCH
              (Telegram LawFirms), Ъ «Сделки года» ($400 млн «согласно открытым источникам»), НедраДВ. Страница
              BIRCH «Энергетика» — не про сделку, заменена постом BIRCH. Планы добычи «более 6 т» и «решения в
              Москве» — ни в одном открытом источнике, сняты. Продавцы — менеджмент и миноритарии без имен.
  gbc0b68bd — Ведомости (ЕГРЮЛ 10 апреля), Retail.ru, New Retail, Sostav. Предмет — ООО «Фэшн фэктори» (ИНН не
              найден). «Не более 150 млн ₽» — оценка Бурмистрова → «До 150 млн ₽ (по оценке)».
  g181d7687 — РБК, Интерфакс, ComNews, CNews (×2), реестр (31.01.2025; 2024: выручка 85,3 млн ₽, прибыль 117 тыс.
              ₽ — в карточке было 323 тыс.). Сумма — оценка Делицына и Замесова.

    python3 pipeline/archive/2026-11/reread_m002.py            # сухой прогон
    python3 pipeline/archive/2026-11/reread_m002.py --write
"""
import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PIPE = os.path.dirname(os.path.dirname(HERE))
ROOT = os.path.dirname(PIPE)
for p in (os.path.join(PIPE, 'ingest'), PIPE, ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)
DATA = os.environ.get('M002_DATA') or os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
_BY = 'reread_m002'

ONE_OFF = [('gfa14411d',
  'title',
  'Польская LPP Group продала российскую сеть Reserved компании Far East Services FZCO',
  'Far East Services FZCO купил 95% «РЕ Трэйдинг» у LPP',
  'Новым владельцем ООО «РЕ Трэйдинг» — российского подразделения LPP стала зарегистрированная в ОАЭ компания «Фар '
  'ист сервисиз-фзко». Запись об этом в ЕГРЮЛ датирована 30 июня. Там указывается, что «Фар ист сервисиз-фзко» '
  'получила 95% «РЕ Трэйдинг», еще 5% перешли гендиректору российского дивизиона LPP Анне Пилюгиной … Legal support '
  'for a transaction that involved LPP S.A., one of the largest global retailers (known for brands such as Reserved, '
  'House, Cropp, Mohito, and Sinsay), selling its Russian subsidiary, LLC RE Trading, to a consortium of Chinese '
  'investors.',
  'https://www.kommersant.ru/doc/5446520'),
 ('gfa14411d',
  'date',
  '2022-05-23',
  '2022-06-30',
  'Новым владельцем ООО «РЕ Трэйдинг» — российского подразделения LPP стала зарегистрированная в ОАЭ компания «Фар '
  'ист сервисиз-фзко». Запись об этом в ЕГРЮЛ датирована 30 июня. Там указывается, что «Фар ист сервисиз-фзко» '
  'получила 95% «РЕ Трэйдинг», еще 5% перешли гендиректору российского дивизиона LPP Анне Пилюгиной',
  'https://www.kommersant.ru/doc/5446520'),
 ('gfa14411d',
  'seller',
  'ООО «РЕ Трэйдинг», LPP SA',
  'LPP SA',
  'Legal support for a transaction that involved LPP S.A., one of the largest global retailers (known for brands '
  'such as Reserved, House, Cropp, Mohito, and Sinsay), selling its Russian subsidiary, LLC RE Trading, to a '
  'consortium of Chinese investors.',
  'https://www.pgplaw.com/upload/iblock/0c7/qtphlbgforz2fcytqxc2r7fathr0mtya/2025_Corporate_eng.pdf'),
 ('gfa14411d',
  'eco.share',
  '—',
  '95% долей ООО «РЕ Трэйдинг»',
  'Новым владельцем ООО «РЕ Трэйдинг» — российского подразделения LPP стала зарегистрированная в ОАЭ компания «Фар '
  'ист сервисиз-фзко». Запись об этом в ЕГРЮЛ датирована 30 июня. Там указывается, что «Фар ист сервисиз-фзко» '
  'получила 95% «РЕ Трэйдинг», еще 5% перешли гендиректору российского дивизиона LPP Анне Пилюгиной',
  'https://www.kommersant.ru/doc/5446520'),
 ('gfa14411d',
  'law.adv',
  [['Юридический консультант продавца (ООО «РЕ Трэйдинг», LPP SA)',
    'Пепеляев Групп',
    'Продажа Reserved Far East Services FZCO. Источник: pgplaw.ru']],
  [['Юридический консультант продаваемой компании (ООО «РЕ Трэйдинг»)',
    'Пепеляев Групп',
    'Сопровождение продажи ООО «РЕ Трэйдинг» консорциуму китайских инвесторов, защита интересов «РЕ Трэйдинг» на '
    'переговорах. Источник: pgplaw.com']],
  'Legal support for a transaction that involved LPP S.A., one of the largest global retailers (known for brands '
  'such as Reserved, House, Cropp, Mohito, and Sinsay), selling its Russian subsidiary, LLC RE Trading, to a '
  'consortium of Chinese investors. … We also safeguarded the interests of LLC RE Trading during negotiations with '
  'the parties involved.',
  'https://www.pgplaw.com/upload/iblock/0c7/qtphlbgforz2fcytqxc2r7fathr0mtya/2025_Corporate_eng.pdf'),
 ('gfa14411d',
  'eco.val',
  '—',
  'По данным отчета Hindenburg Research, LPP разделила сделку на две части: магазины — около $135 млн (601 млн '
  'злотых) с оплатой в рассрочку в течение 4 лет и старые товарные запасы — около $247 млн (1,1 млрд злотых) с '
  'оплатой до конца мая 2023 года. Денег при закрытии покупатель не платил.\n'
  '\n'
  'По данным польского портала WNP.pl, за 100% российской компании стороны согласовали $135,5 млн.',
  'No cash was initially exchanged. The first element, the stores, were sold for ~$135 million ( PLN 601 million ), '
  'to be paid in instalments within 4 years. The second element represented ~$247 million (PLN 1.1 billion) of old '
  'inventory, with the balance to be paid out by the end of May 2023. … The parties eventually agreed on a price of '
  '$135.5 million for 100% of shares in the Russian company.',
  'https://hindenburgresearch.com/lpp/'),
 ('gfa14411d',
  'eco.rationale',
  'LPP Group продала российскую сеть магазинов (Reserved, Cropp, House, Mohito, Sinsay) зарегистрированной в Дубае '
  'Far East Services FZCO. Бенефициарное владение покупателя оспаривается исследованием Hindenburg Research — есть '
  'предположения о связи с прежним менеджментом LPP.',
  'LPP уходила из России: в марте 2022 года компания закрыла все свои российские магазины из-за военной операции на '
  'Украине и прекратила продажи и инвестиции в стране.',
  'Производитель одежды LPP Group закрыл принадлежащие ему магазины в России 29 марта из-за военной операции РФ на '
  'Украине. Компания также остановила все продажи, инвестиции и планы по развитию в стране. … In March 2022, LPP '
  'first announced that it would suspend operations in Russia',
  'https://www.kommersant.ru/doc/5446520'),
 ('gfa14411d',
  'eco.context',
  'Компания FES Retail по примеру других крупных fashion-операторов планирует оптимизировать бизнес, отказавшись от '
  'части своих магазинов. Под закрытие попадает около 50 точек. В марте 2024 года исследовательская компания '
  'Hindenburg Research опубликовала отчет с утверждением, что уход LPP из России был фиктивным: Far East Services '
  'была зарегистрирована в Дубае за день до объявления о сделке, а по данным таможенной статистики, с сентября 2022 '
  'по декабрь 2023 года в Россию через связанные компании было экспортировано товаров LPP на сумму не менее $706,5 '
  'млн. LPP категорически отрицает обвинения, называя отчет организованной атакой на котировки акций, и добилась '
  'расследования против самой Hindenburg по подозрению в манипулировании рынком — следствие польской прокуратуры по '
  'состоянию на середину 2026 года приостановлено в ожидании международной правовой помощи США.',
  'О продаже российского бизнеса «консорциуму из Китая» LPP объявила в мае 2022 года. Far East Services FZCO '
  'зарегистрирована в Дубае 18 мая 2022 года, за день до этого объявления. Прав на товарные знаки LPP покупатель не '
  'получил, и магазины открылись под вывесками Re, M и «Син».\n'
  '\n'
  'В ноябре 2022 года FES Retail, к которой перешли магазины, объявила о закрытии около 50 из более чем 500 точек '
  'из-за невыгодных условий аренды.\n'
  '\n'
  'В марте 2024 года Hindenburg Research заявила, что уход LPP из России фиктивный: по ее подсчетам, после сделки и '
  'до конца 2023 года «РЕ Трэйдинг» ввезла в Россию товаров не меньше чем на $706,5 млн. LPP обвинения отвергла, '
  'назвала отчет попыткой манипулировать курсом акций и обратилась в польскую прокуратуру. В июле 2025 года LPP '
  'согласилась заплатить 1,8 млн злотых, чтобы закрыть расследование финансового регулятора Польши о том, как '
  'компания раскрывала условия продажи.',
  'О планах продать свой российский бизнес консорциуму из Китая LPP говорил еще в мае. … Far East Services – FZCO '
  'was incorporated in Dubai on May 18 th , 2022, one day before LPP announced it had concluded negotiations for '
  'selling its Russian assets … Права на использование товарных знаков и брендов, которыми владеет LPP, новый '
  'собственник не получит, заявлял ранее ритейлер. Сейчас магазины розничной компании возобновили работу, но под '
  'другими вывесками: Reserved получил название Re, Mohito — M, а Sinsay — «Син». … Компания из ОАЭ FES Retail, '
  'владеющая брендами Reserved, Cropp, House, Mohito и Sinsay, планирует закрыть около 50 магазинов в России. Это '
  'связано с невыгодными условиями аренды. … Вместо этого компания сосредоточится на других торговых точках, которых '
  'насчитывается более 500. … However, in March 2024, Hindenburg Research alleged that the divestment was a façade … '
  'That means in the entire period since divestment until the end of 2023, RE Trading imported to Russia a total of '
  'at least $706.5 million of merchandise. … LPP has strongly denied the accusations, calling the report a '
  '“disinformation attack” aimed at manipulating its stock price. The company reported the matter to Polish '
  'prosecutors. … has agreed to pay a 1.8 million zloty (€420,000) fine to settle an investigation by Poland’s '
  'financial regulator into suspected failings by the company to meet disclosure obligations during the sale of its '
  'Russian business … Jul 11, 2025',
  'https://hindenburgresearch.com/lpp/'),
 ('gfa14411d',
  'law.terms',
  'У нового покупателя также есть опцион на обратную продажу компании LPP до конца 2026 года, что дает LPP '
  'возможность вернуть себе российский бизнес после окончания войны.',
  'По данным Hindenburg Research, у покупателя есть опцион продать компанию обратно LPP до конца 2026 года. '
  'Консультант «РЕ Трэйдинг» Пепеляев Групп подтверждает, что сделка предусматривает возможность вернуться в капитал '
  'в оговоренный срок.',
  'The new buyer also has the option of selling the company back to LPP by the end of 2026 … Like many similar '
  'transactions, this one involved an option for a potential return as a shareholder within an agreed period.',
  'https://hindenburgresearch.com/lpp/'),
 ('gfa14411d',
  'extra',
  'LPP Group продала российскую сеть магазинов (Reserved, Cropp, House, Mohito, Sinsay) зарегистрированной в Дубае '
  'Far East Services FZCO. Бенефициарное владение покупателя оспаривается исследованием Hindenburg Research — есть '
  'предположения о связи с прежним менеджментом LPP. Сведения сверены с трекером KSE Institute «Leave Russia» и '
  'независимой прессой там, где это было возможно.',
  'LPP получала оплату за российский бизнес в рассрочку, а у покупателя остался опцион вернуть компанию LPP. '
  'Польский финансовый регулятор расследовал, вовремя ли LPP раскрыла ключевые условия и структуру этой продажи.',
  'No cash was initially exchanged. The first element, the stores, were sold for ~$135 million ( PLN 601 million ), '
  'to be paid in instalments within 4 years. The second element represented ~$247 million (PLN 1.1 billion) of old '
  'inventory, with the balance to be paid out by the end of May 2023. … The new buyer also has the option of selling '
  'the company back to LPP by the end of 2026 … did not publicly disclose information regarding the key terms and '
  'structure of the sale of its Russian subsidiary, Re Trading OOO, in 2022',
  'https://notesfrompoland.com/2025/07/11/polish-retail-giant-lpp-accepts-1-8m-zloty-fine-over-disclosure-failings-linked-to-russia-exit/'),
 ('g55f1c662',
  'title',
  'Финская Valio продала российский бизнес (бренд Viola) компании Velcom',
  '«Дэнир» купил российский бизнес Valio',
  'С 29 декабря 2022 года владельцем бывшей российской «дочки» Valio — ООО «Виола» — стало ООО «Дэнир» , которое '
  'принадлежит бенефициару ГК «Велком»',
  'https://www.retail.ru/news/rossiyskaya-dochka-valio-pereshla-v-sobstvennost-benefitsiara-velkoma-12-yanvarya-2023-224567/'),
 ('g55f1c662',
  'date',
  '2022-06-01',
  '2022-12-29',
  'С 29 декабря 2022 года владельцем бывшей российской «дочки» Valio — ООО «Виола» — стало ООО «Дэнир» , которое '
  'принадлежит бенефициару ГК «Велком» … 29 декабря 2022 года — АО "РУСХОЛД М" (RUSHOLD M OY) вышел из состава '
  'участников доля 100.0%. 29 декабря 2022 года — ООО "ДЭНИР" вошел в состав участников доля 100.0%.',
  'https://www.retail.ru/news/rossiyskaya-dochka-valio-pereshla-v-sobstvennost-benefitsiara-velkoma-12-yanvarya-2023-224567/'),
 ('g55f1c662',
  'eco.share',
  '—',
  '100% долей ООО «Виола» (до октября 2022 года — ООО «Валио»)',
  '29 декабря 2022 года — АО "РУСХОЛД М" (RUSHOLD M OY) вышел из состава участников доля 100.0%. 29 декабря 2022 '
  'года — ООО "ДЭНИР" вошел в состав участников доля 100.0%. … В октябре прошлого года ООО «Валио» сменило название '
  'на ООО «Виола». … С 29 декабря 2022 года владельцем бывшей российской «дочки» Valio — ООО «Виола» — стало ООО '
  '«Дэнир» , которое принадлежит бенефициару ГК «Велком»',
  'https://projectcompass.ru/api/companies/g54913880/fns'),
 ('g55f1c662',
  'eco.target_fin',
  'Российский бизнес давал Valio около 5% мировых продаж: в 2020 г. это 85 млн евро из 1,8 млрд евро у всего '
  'концерна.',
  'Российский бизнес давал Valio около 5% мировых продаж: в 2020 году — €87 млн из примерно €1,8 млрд.',
  'In 2020, Valio’s net sales in Russia were EUR 87 million and accounted for approximately 5 per cent of Valio’s '
  'global net sales of about EUR 1.8 billion.',
  'https://castren.fi/cases/cases-2022/valio3'),
 ('g55f1c662',
  'eco.context',
  '7 марта финский концерн принял решение завершить деятельность в России на фоне военной спецоперации. Спустя '
  'несколько дней российское подразделение концерна ООО «Валио» заявило, что продолжит операционную деятельность. По '
  'неофициальным данным, новым владельцем бизнеса могла стать группа «Русагро». После сделки 2024 год «Виола» '
  '(бывшая «Валио») завершила с чистым убытком 19,8 млн ₽ против чистой прибыли 295,8 млн ₽ годом ранее — первым '
  'убытком за долгое время; выручка при этом выросла почти на 26%, до 11,3 млрд ₽. В 2025 году компания показала '
  'рекордные результаты: выручка достигла 12,3 млрд ₽ (максимум за пять лет), чистая прибыль — 90,2 млн ₽.',
  'Решение уйти из России Valio приняла 7 марта 2022 года; переговоры с группой «Велком» о продаже бизнеса '
  'закончились в апреле. В октябре 2022 года ООО «Валио» переименовали в ООО «Виола».\n'
  '\n'
  'После сделки «Виола» закончила 2024 год с чистым убытком 19,8 млн ₽ против прибыли 295,8 млн ₽ годом ранее, хотя '
  'выручка выросла почти на 26%, до 11,3 млрд ₽. В 2025 году выручка достигла 12,3 млрд ₽, чистая прибыль — 90,2 млн '
  '₽.',
  'On 7 March 2022, Valio decided to withdraw from operations in Russia. … В апреле он завершил переговоры о продаже '
  'бизнеса ГК «Велком». … В октябре прошлого года ООО «Валио» сменило название на ООО «Виола». … завершил 2024 год с '
  'чистым убытком в 19,8 млн рублей против чистой прибыли в 295,8 млн рублей годом ранее … выручка компании в 2024 '
  'году выросла почти на 26%, до 11,3 млрд рублей … В 2025 году компания «Виола», выпускающая молочную продукцию, '
  'достигла рекордных финансовых результатов … достигла 12,3 млрд рублей (максимум за пять лет), чистая прибыль '
  'составила 90,2 млн рублей',
  'https://www.interfax.ru/business/1018641'),
 ('g55f1c662',
  'law.struct',
  'Покупатель получает марку Viola и завод в подмосковном Ершово, где делают плавленые и полутвердые сыры; весь '
  'коллектив остается. С 29 декабря 2022 г. ООО «Виола» принадлежит ООО «Дэнир», которым владеет бенефициар ГК '
  '«Велком».',
  'Покупатель получил сырный завод в Ершово под Москвой, где выпускают плавленые и полутвердые сыры, и российские '
  'права на бренд Viola. 29 декабря 2022 года 100% ООО «Виола» перешли от финской Rushold M Oy (АО «Русхолд М») к '
  'ООО «Дэнир», которое принадлежит бенефициару группы «Велком».',
  'В сделку вошли завод по производству плавленых и полутвердых сыров в Ершово (Московская область) и права на бренд '
  'плавленых сыров Viola. … 29 декабря 2022 года — АО "РУСХОЛД М" (RUSHOLD M OY) вышел из состава участников доля '
  '100.0%. 29 декабря 2022 года — ООО "ДЭНИР" вошел в состав участников доля 100.0%. … С 29 декабря 2022 года '
  'владельцем бывшей российской «дочки» Valio — ООО «Виола» — стало ООО «Дэнир» , которое принадлежит бенефициару ГК '
  '«Велком»',
  'https://www.retail.ru/news/rossiyskaya-dochka-valio-pereshla-v-sobstvennost-benefitsiara-velkoma-12-yanvarya-2023-224567/'),
 ('g55f1c662',
  'law.terms',
  'Стороны условились держать цену и прочие условия в тайне.',
  '—',
  'С 29 декабря 2022 года владельцем бывшей российской «дочки» Valio — ООО «Виола» — стало ООО «Дэнир» , которое '
  'принадлежит бенефициару ГК «Велком»',
  'https://www.retail.ru/news/rossiyskaya-dochka-valio-pereshla-v-sobstvennost-benefitsiara-velkoma-12-yanvarya-2023-224567/'),
 ('g55f1c662',
  'extra',
  'Финская молочная компания Valio продала российский бизнес под брендом Viola компании Velcom, уходя с российского '
  'рынка. Сделка отражена в трекере KSE Institute «Leave Russia» и сверена с независимой прессой там, где это было '
  'возможно.',
  'Valio вышла из России, продав сырный завод в Ершово и бренд Viola структуре владельца группы «Велком» — '
  'производителя колбасных изделий из Центральной России.',
  'В сделку вошли завод по производству плавленых и полутвердых сыров в Ершово (Московская область) и права на бренд '
  'плавленых сыров Viola. … С 29 декабря 2022 года владельцем бывшей российской «дочки» Valio — ООО «Виола» — стало '
  'ООО «Дэнир» , которое принадлежит бенефициару ГК «Велком» … один из крупных производителей колбасных изделий в '
  'Центральном федеральном округе РФ',
  'https://www.retail.ru/news/rossiyskaya-dochka-valio-pereshla-v-sobstvennost-benefitsiara-velkoma-12-yanvarya-2023-224567/'),
 ('g57b3b93c',
  'title',
  'Mayr-Melnhof Group продала российские заводы MM Packaging компании Granelle',
  '«Гранель» купила у Mayr-Melnhof заводы «ММПОФ Пэкэджинг» и «ММПОФ Ротогравюр»',
  'приобрела на Северо-Западе три завода по выпуску бумаги и картона: в Ломоносовском районе Ленобласти «ММПОФ '
  'Пэкэджинг» и «ММПОФ Ротогравюр» и «Невские грани» во Пскове. … До начала СВО компаниями «ММПОФ Пэкэджинг» '
  '(выручка за 2023 год 7,9 млрд руб.) и «ММПОФ Ротогравюр» (4,2 млрд руб.) на 99,99 % владела австрийская компания '
  'MM PACKAGING GmbH, оставшаяся часть принадлежала MM BOARD & PAPER GmbH. «Невскими гранями» (выручка 2,3 млрд '
  'руб.) распоряжалась австрийская TANNPAPIER GmbH. В декабре 2022 года все три компании в полном объеме перешли к '
  'московской ГК «Гранель», а следом в марте 2023-го — к ООО «Форвард». По данным СПАРК, главным бенефициаром с '
  'долей 99,99 % «Форварда» «Свеза» стала еще 27 декабря прошлого года. … has sold its two Packaging sites in '
  'Russia, St. Petersburg and Pskov, to the local investor Granelle following approval by the governmental '
  'authorities. The selling price amounts to approx. EUR 134 million. In 2021, the plants generated combined sales '
  'of approx. EUR 124 million.',
  'https://www.fontanka.ru/2025/01/11/74977775/'),
 ('g57b3b93c',
  'date',
  '2022-12-01',
  '2022-12-16',
  'Pressemitteilung - 16. Dezember 2022 Die Mayr-Melnhof Gruppe (MM), ein weltweit führender Hersteller von Karton '
  'und Faltschachteln, hat ihre beiden Packaging-Standorte in Russland, St. Petersburg und Pskov, nach erfolgter '
  'Genehmigung durch die Behörden an den lokalen Investor Granelle verkauft.',
  'https://cms.law/de/aut/news-information/mayr-melnhof-packaging-verkauft-russische-standorte-mit-rechtlicher-begleitung-von-cms'),
 ('g57b3b93c',
  'eco.share',
  '—',
  '100% компаний «ММПОФ Пэкэджинг» и «ММПОФ Ротогравюр»',
  'До начала СВО компаниями «ММПОФ Пэкэджинг» (выручка за 2023 год 7,9 млрд руб.) и «ММПОФ Ротогравюр» (4,2 млрд '
  'руб.) на 99,99 % владела австрийская компания MM PACKAGING GmbH, оставшаяся часть принадлежала MM BOARD & PAPER '
  'GmbH. «Невскими гранями» (выручка 2,3 млрд руб.) распоряжалась австрийская TANNPAPIER GmbH. В декабре 2022 года '
  'все три компании в полном объеме перешли к московской ГК «Гранель», а следом в марте 2023-го — к ООО «Форвард». '
  'По данным СПАРК, главным бенефициаром с долей 99,99 % «Форварда» «Свеза» стала еще 27 декабря прошлого года.',
  'https://www.fontanka.ru/2025/01/11/74977775/'),
 ('g57b3b93c',
  'eco.target_fin',
  '—',
  'В 2021 году два завода вместе выручили около €124 млн. В 2023 году выручка «ММПОФ Пэкэджинг» составила 7,9 млрд '
  '₽, «ММПОФ Ротогравюр» — 4,2 млрд ₽.',
  'has sold its two Packaging sites in Russia, St. Petersburg and Pskov, to the local investor Granelle following '
  'approval by the governmental authorities. The selling price amounts to approx. EUR 134 million. In 2021, the '
  'plants generated combined sales of approx. EUR 124 million. … До начала СВО компаниями «ММПОФ Пэкэджинг» (выручка '
  'за 2023 год 7,9 млрд руб.) и «ММПОФ Ротогравюр» (4,2 млрд руб.) на 99,99 % владела австрийская компания MM '
  'PACKAGING GmbH, оставшаяся часть принадлежала MM BOARD & PAPER GmbH. «Невскими гранями» (выручка 2,3 млрд руб.) '
  'распоряжалась австрийская TANNPAPIER GmbH. В декабре 2022 года все три компании в полном объеме перешли к '
  'московской ГК «Гранель», а следом в марте 2023-го — к ООО «Форвард». По данным СПАРК, главным бенефициаром с '
  'долей 99,99 % «Форварда» «Свеза» стала еще 27 декабря прошлого года.',
  'https://mm.group/news/press-releases/mm-packaging-divests-production-sites-in-russia/'),
 ('g57b3b93c',
  'eco.rationale',
  'Австрийская Mayr-Melnhof Group продала российские упаковочные заводы (MM Packaging) в Санкт-Петербурге и Пскове '
  'локальному инвестору Granelle.',
  '—',
  'has sold its two Packaging sites in Russia, St. Petersburg and Pskov, to the local investor Granelle following '
  'approval by the governmental authorities. The selling price amounts to approx. EUR 134 million. In 2021, the '
  'plants generated combined sales of approx. EUR 124 million.',
  'https://mm.group/news/press-releases/mm-packaging-divests-production-sites-in-russia/'),
 ('g57b3b93c',
  'eco.context',
  'Группа компаний Mayr-Melnhof (MM) продала свои предприятия в Санкт-Петербурге и Пскове местному инвестору '
  'Granelle после одобрения властей. В декабре 2024 года ГК «Гранель» перепродала все три предприятия (в их числе '
  'псковское «Танн Невский», к тому моменту переименованное в «Невские Грани») лесопромышленному холдингу «Свеза» — '
  'подробности этой более поздней сделки приведены в разделе «Этапы сделки», сумму стороны не раскрыли.',
  'До сделки 99,99% «ММПОФ Пэкэджинг» и «ММПОФ Ротогравюр» принадлежали австрийской MM Packaging GmbH, остальное — '
  'MM Board & Paper GmbH. В том же декабре 2022 года к «Гранели» перешло и псковское предприятие «Невские грани», '
  'которым владела австрийская Tannpapier GmbH.\n'
  '\n'
  'В марте 2023 года все три компании перешли к ООО «Форвард», а 27 декабря 2024 года основным бенефициаром '
  '«Форварда» (99,99%) стала лесопромышленная группа «Свеза».',
  'До начала СВО компаниями «ММПОФ Пэкэджинг» (выручка за 2023 год 7,9 млрд руб.) и «ММПОФ Ротогравюр» (4,2 млрд '
  'руб.) на 99,99 % владела австрийская компания MM PACKAGING GmbH, оставшаяся часть принадлежала MM BOARD & PAPER '
  'GmbH. «Невскими гранями» (выручка 2,3 млрд руб.) распоряжалась австрийская TANNPAPIER GmbH. В декабре 2022 года '
  'все три компании в полном объеме перешли к московской ГК «Гранель», а следом в марте 2023-го — к ООО «Форвард». '
  'По данным СПАРК, главным бенефициаром с долей 99,99 % «Форварда» «Свеза» стала еще 27 декабря прошлого года. … '
  'has sold its two Packaging sites in Russia, St. Petersburg and Pskov, to the local investor Granelle following '
  'approval by the governmental authorities. The selling price amounts to approx. EUR 134 million. In 2021, the '
  'plants generated combined sales of approx. EUR 124 million. … «Свеза» купила три завода на Северо-Западе - 11 '
  'января 2025',
  'https://www.fontanka.ru/2025/01/11/74977775/'),
 ('g57b3b93c',
  'extra',
  'Австрийская Mayr-Melnhof Group продала российские упаковочные заводы (MM Packaging) в Санкт-Петербурге и Пскове '
  'локальному инвестору Granelle. Сведения взяты из трекера KSE Institute «Leave Russia» и сверены с независимой '
  'прессой там, где это было возможно.',
  'Mayr-Melnhof продала два российских упаковочных завода девелоперу «Гранель» примерно за €134 млн, через два года '
  'их купила «Свеза».',
  'has sold its two Packaging sites in Russia, St. Petersburg and Pskov, to the local investor Granelle following '
  'approval by the governmental authorities. The selling price amounts to approx. EUR 134 million. In 2021, the '
  'plants generated combined sales of approx. EUR 124 million. … In December 2022, they were sold to the Granel '
  'development company for 134 million euros. … приобрела на Северо-Западе три завода по выпуску бумаги и картона: в '
  'Ломоносовском районе Ленобласти «ММПОФ Пэкэджинг» и «ММПОФ Ротогравюр» и «Невские грани» во Пскове.',
  'https://mm.group/news/press-releases/mm-packaging-divests-production-sites-in-russia/'),
 ('g1059432d',
  'title',
  'Whirlpool продала российский завод и бренды Hotpoint/Indesit турецкой Arçelik',
  'Arçelik купил «Индезит Интернэшнл» и «Вирлпул Рус» у Whirlpool',
  'По данным ЕГРЮЛ, с 16 сентября текущего года 100% уставного капитала АО «Индезит Интернэшнл» и с 7 сентября 100% '
  'уставного капитала ООО «Вирлпул Рус» принадлежат Arcelik Anonim Sirketi … On August 31, 2022, we completed the '
  'sale to Arcelik.',
  'https://www.retail.ru/news/turetskaya-kompaniya-arcelik-stala-vladeltsem-rossiyskogo-biznesa-whirlpool-28-sentyabrya-2022-220964/'),
 ('g1059432d',
  'date',
  '2022-11-01',
  '2022-08-31',
  'On August 31, 2022, we completed the sale to Arcelik.',
  'https://www.sec.gov/Archives/edgar/data/106640/000010664022000138/whr-20220930.htm'),
 ('g1059432d',
  'sum',
  '€220 млн',
  'Не раскрыта',
  'Additionally, the contingent consideration is subject to a cap based on the agreed net asset value of the Russian '
  'business as of closing. The net asset value is currently estimated at € 220 million … Additionally, the '
  'contingent consideration is subject to a cap based on the agreed net asset value of the Russia business of € 261 '
  'million at closing',
  'https://www.sec.gov/Archives/edgar/data/106640/000010664023000131/whr-20230930.htm'),
 ('g1059432d',
  'eco.sum',
  '€220 млн',
  'Не раскрыта',
  'Additionally, the contingent consideration is subject to a cap based on the agreed net asset value of the Russian '
  'business as of closing. The net asset value is currently estimated at € 220 million … Additionally, the '
  'contingent consideration is subject to a cap based on the agreed net asset value of the Russia business of € 261 '
  'million at closing',
  'https://www.sec.gov/Archives/edgar/data/106640/000010664023000131/whr-20230930.htm'),
 ('g1059432d',
  'eco.share',
  'Помимо России, приобретенные Arcelik компании работают в Киргизии, Таджикистане, Туркмении, Узбекистане, Армении, '
  'Грузии, Азербайджане, Казахстане, Белоруссии и Монголии.',
  '100% акций АО «Индезит Интернэшнл» и 100% долей ООО «Вирлпул Рус»',
  'По данным ЕГРЮЛ, с 16 сентября текущего года 100% уставного капитала АО «Индезит Интернэшнл» и с 7 сентября 100% '
  'уставного капитала ООО «Вирлпул Рус» принадлежат Arcelik Anonim Sirketi',
  'https://www.retail.ru/news/turetskaya-kompaniya-arcelik-stala-vladeltsem-rossiyskogo-biznesa-whirlpool-28-sentyabrya-2022-220964/'),
 ('g1059432d',
  'eco.val',
  '—',
  'Фиксированной цены стороны не назначали: выплаты зависели от результатов российского бизнеса и были ограничены '
  'согласованной стоимостью его чистых активов на дату закрытия. При подписании Arçelik сообщала, что сумма не '
  'превысит €220 млн; по отчетности Whirlpool за 2023 год этот предел составил €261 млн.',
  'Представители Arcelik ранее сообщали, что сумма сделки не превысит 220 млн евро. … Additionally, the contingent '
  'consideration is subject to a cap based on the agreed net asset value of the Russian business as of closing. The '
  'net asset value is currently estimated at € 220 million … Additionally, the contingent consideration is subject '
  'to a cap based on the agreed net asset value of the Russia business of € 261 million at closing … Whirlpool '
  'Corporation — Form 10-Q, Q3 2023',
  'https://www.sec.gov/Archives/edgar/data/106640/000010664023000131/whr-20230930.htm'),
 ('g1059432d',
  'law.terms',
  'Изначальные условия сделки были заметно сложнее фиксированной суммы: итоговая стоимость актива должна была '
  'определяться на протяжении десяти лет после закрытия и зависела от финансовых показателей бизнеса и ряда '
  'дополнительных условий. Стороны решили упростить механизм расчетов и заменить его разовым платежом €40 млн. К '
  'марту 2026 года Arçelik уже накопила по этому соглашению долгосрочные обязательства примерно на €117 млн, так что '
  'новая договоренность почти втрое сократила итоговую сумму выплат. Общая сумма выплат (около €157 млн: €117 млн '
  'накопленных обязательств плюс €40 млн разового платежа) укладывается в объявленный при подписании максимум — по '
  'словам представителей Arçelik, «сумма сделки не превысит 220 млн евро».',
  'Выплаты Arçelik зависели от результатов российского бизнеса и были растянуты на 10 лет. В июне 2026 года Arçelik '
  'сообщила, что закрыла все обязательства по этой покупке последним платежом €40 млн.',
  'Сообщается, что стоимость сделки не превысит 220 млн евро, а выплаты будут растянуты на 10 лет. … The company '
  "also said it had completed all payment obligations related to its 2022 acquisition of Indesit and Whirlpool's "
  'operations in Russia, with a final payment of 40 million euros. … Jun 19, 2026',
  'https://www.dailysabah.com/business/economy/turkish-home-appliance-maker-arcelik-takes-full-control-of-beko-europe'),
 ('g1059432d',
  'law.struct',
  'Турецкая Arçelik подписала с Whirlpool EMEA S.p.A. соглашение о покупке ее российских активов — АО «Индезит '
  'Интернэшнл» и ООО «Вирлпул Рус».',
  'Whirlpool EMEA S.p.A. подписала договор о продаже 27 июня 2022 года, сделка закрыта 31 августа 2022 года. В ЕГРЮЛ '
  'переход 100% ООО «Вирлпул Рус» записан 7 сентября, 100% акций АО «Индезит Интернэшнл» — 16 сентября 2022 года.',
  'was signed on 27 June 2022 … On August 31, 2022, we completed the sale to Arcelik. … По данным ЕГРЮЛ, с 16 '
  'сентября текущего года 100% уставного капитала АО «Индезит Интернэшнл» и с 7 сентября 100% уставного капитала ООО '
  '«Вирлпул Рус» принадлежат Arcelik Anonim Sirketi',
  'https://betterchance.ru/en/news/better-chance-advises-arcelik-a-/'),
 ('g1059432d',
  'eco.rationale',
  'Американская Whirlpool продала завод бытовой техники в Липецке и права на бренды Hotpoint и Indesit в России '
  'турецкой Arçelik A.Ş. за €220 млн.',
  '—',
  'В начале марта 2022 года Whirlpool объявила о приостановке производства в России из-за снижения спроса.',
  'https://www.tadviser.ru/index.php/Компания:IHPA_-_IHP_Appliances_Sales_-_Ай_Эйч_Пи_Апплаенсес_Сейлс_-_Вирлпул_Рус_(Whirlpool_Rus)'),
 ('g1059432d',
  'eco.context',
  'Оба юрлица теперь принадлежат турецкой АК «Арчелик» как единственному учредителю и сменили названия. Липецкое АО '
  '«Индезит Интернэшнл» стало АО «Ай эйч пи апплаенсес» (IHP Appliances), московское ООО «Вирлпул Рус» — ООО «Ай эйч '
  'пи апплаенсес».',
  'В начале марта 2022 года Whirlpool приостановила производство в России из-за падения спроса. Arçelik получила '
  'липецкие заводы мощностью 2,8 млн холодильников и стиральных машин в год, российские права на бренды Indesit, '
  'Hotpoint и Stinol, а также продажи в Казахстане и других странах СНГ: кроме России, купленные компании работают в '
  'Киргизии, Таджикистане, Туркмении, Узбекистане, Армении, Грузии, Азербайджане, Белоруссии и Монголии.\n'
  '\n'
  'После сделки оба юрлица сменили названия: АО «Индезит Интернэшнл» стало АО «Ай эйч пи апплаенсес», ООО «Вирлпул '
  'Рус» — ООО «Ай эйч пи апплаенсес». Единственный учредитель обоих — Arçelik.',
  'В начале марта 2022 года Whirlpool объявила о приостановке производства в России из-за снижения спроса. … '
  'позволяющие выпускать 2,8 млн холодильников и стиральных машин в год … Вместе с приобретением компаний турецкий '
  'производитель сможет использовать бренды Indesit и Hotpoint. Сделка также распространяется на бренд Stinol. … '
  'Помимо России, приобретенные Arcelik компании работают в Киргизии, Таджикистане, Туркмении, Узбекистане, Армении, '
  'Грузии, Азербайджане, Казахстане, Белоруссии и Монголии. … Липецкое АО «Индезит Интернэшнл» было переименовано в '
  'АО «Ай эйч пи апплаенсес» (IHP Appliances). Зарегистрированное в Москве ООО «Вирлпул Рус» теперь носит название '
  'ООО «Ай эйч пи апплаенсес». Единственным учредителем этих юрлиц выступает акционерная компания «Арчелик»',
  'https://www.retail.ru/news/turetskaya-kompaniya-arcelik-stala-vladeltsem-rossiyskogo-biznesa-whirlpool-28-sentyabrya-2022-220964/'),
 ('g1059432d',
  'extra',
  'Американская Whirlpool продала турецкой Arçelik A.Ş. завод бытовой техники в Липецке и права на бренды Hotpoint и '
  'Indesit в России; сумма сделки — €220 млн. Сделка отражена в трекере уходов компаний с российского рынка KSE '
  'Institute «Leave Russia».',
  'Arçelik получила липецкие заводы Whirlpool и российские права на Indesit, Hotpoint и Stinol без фиксированной '
  'цены: расчеты зависели от результатов бизнеса.',
  'Вместе с приобретением компаний турецкий производитель сможет использовать бренды Indesit и Hotpoint. Сделка '
  'также распространяется на бренд Stinol. … Сообщается, что стоимость сделки не превысит 220 млн евро, а выплаты '
  'будут растянуты на 10 лет.',
  'https://www.tadviser.ru/index.php/Компания:IHPA_-_IHP_Appliances_Sales_-_Ай_Эйч_Пи_Апплаенсес_Сейлс_-_Вирлпул_Рус_(Whirlpool_Rus)'),
 ('gfc7e5649',
  'buyer',
  'g66a64a9f',
  None,
  'Российские частные инвесторы, совладельцы компании-интегратора Awara IT Group Александр Ермаков и Юрий Шумаков '
  'купили ООО "СофтварэУАН" (SoftwareONE Russia). Доли партнеров распределены как 60% и 40% соответственно. … 19 мая '
  '2022 года — СОФТВЭРУАН АГ вышел из состава участников доля 100.0%. 19 мая 2022 года — Ермаков Александр '
  'Владимирович вошел в состав участников доля 60.0%. 19 мая 2022 года — Шумаков Юрий Алексеевич вошел в состав '
  'участников доля 40.0%.',
  'https://projectcompass.ru/api/companies/ge90270b7/fns'),
 ('gfc7e5649',
  'buyer_name',
  None,
  'Александр Ермаков и Юрий Шумаков (совладельцы Awara IT Group)',
  'Российские частные инвесторы, совладельцы компании-интегратора Awara IT Group Александр Ермаков и Юрий Шумаков '
  'купили ООО "СофтварэУАН" (SoftwareONE Russia). Доли партнеров распределены как 60% и 40% соответственно. … 19 мая '
  '2022 года — СОФТВЭРУАН АГ вышел из состава участников доля 100.0%. 19 мая 2022 года — Ермаков Александр '
  'Владимирович вошел в состав участников доля 60.0%. 19 мая 2022 года — Шумаков Юрий Алексеевич вошел в состав '
  'участников доля 40.0%.',
  'https://www.comnews.ru/content/220241/2022-05-17/2022-w20/awara-it-poglotila-aktivy-softwareone-rossii'),
 ('gfc7e5649',
  'title',
  'SoftwareONE продала российский бизнес по лицензированию ПО компании Awara IT Group',
  'Александр Ермаков и Юрий Шумаков купили SoftwareONE Russia',
  'Российские частные инвесторы, совладельцы компании-интегратора Awara IT Group Александр Ермаков и Юрий Шумаков '
  'купили ООО "СофтварэУАН" (SoftwareONE Russia). Доли партнеров распределены как 60% и 40% соответственно.',
  'https://www.comnews.ru/content/220241/2022-05-17/2022-w20/awara-it-poglotila-aktivy-softwareone-rossii'),
 ('gfc7e5649',
  'date',
  '2022-07-01',
  '2022-05-19',
  '19 мая 2022 года — СОФТВЭРУАН АГ вышел из состава участников доля 100.0%. 19 мая 2022 года — Ермаков Александр '
  'Владимирович вошел в состав участников доля 60.0%. 19 мая 2022 года — Шумаков Юрий Алексеевич вошел в состав '
  'участников доля 40.0%.',
  'https://projectcompass.ru/api/companies/ge90270b7/fns'),
 ('gfc7e5649',
  'eco.share',
  '—',
  '100% долей ООО «СофтвэрУАН» (теперь ООО «Ван Ай Ти Трейд»): 60% у Александра Ермакова, 40% у Юрия Шумакова',
  'Российские частные инвесторы, совладельцы компании-интегратора Awara IT Group Александр Ермаков и Юрий Шумаков '
  'купили ООО "СофтварэУАН" (SoftwareONE Russia). Доли партнеров распределены как 60% и 40% соответственно. … 19 мая '
  '2022 года — СОФТВЭРУАН АГ вышел из состава участников доля 100.0%. 19 мая 2022 года — Ермаков Александр '
  'Владимирович вошел в состав участников доля 60.0%. 19 мая 2022 года — Шумаков Юрий Алексеевич вошел в состав '
  'участников доля 40.0%. … ООО «ВАН АЙ ТИ ТРЕЙД», ИНН 5044057860',
  'https://www.comnews.ru/content/220241/2022-05-17/2022-w20/awara-it-poglotila-aktivy-softwareone-rossii'),
 ('gfc7e5649',
  'law.adv',
  [['Стороны сделки', 'Не раскрывались', 'Юридические консультанты в публичных источниках не раскрывались']],
  [],
  'Российские частные инвесторы, совладельцы компании-интегратора Awara IT Group Александр Ермаков и Юрий Шумаков '
  'купили ООО "СофтварэУАН" (SoftwareONE Russia). Доли партнеров распределены как 60% и 40% соответственно.',
  'https://www.comnews.ru/content/220241/2022-05-17/2022-w20/awara-it-poglotila-aktivy-softwareone-rossii'),
 ('gfc7e5649',
  'law.struct',
  'По данным ЕГРЮЛ, участники компании — Александр Ермаков с 56%-ной долей, Юрий Шумаков с 30%-ной и Александр '
  'Пирогов с 14%. Выручка ООО «Авара Ай Ти Солюшенс» по итогам 2020 года составила 271,7 млн ₽, за 2021 год — 297 '
  'млн ₽.',
  'SoftwareONE AG продала 100% российской компании ООО «СофтвэрУАН» не самой Awara IT, а двум ее совладельцам: 60% '
  'получил Александр Ермаков, 40% — Юрий Шумаков. В ЕГРЮЛ переход записан 19 мая 2022 года. Компанию переименовали в '
  'ООО «Ван Ай Ти Трейд», российский бизнес Awara IT вошел в нее под брендом WONE IT.',
  'Российские частные инвесторы, совладельцы компании-интегратора Awara IT Group Александр Ермаков и Юрий Шумаков '
  'купили ООО "СофтварэУАН" (SoftwareONE Russia). Доли партнеров распределены как 60% и 40% соответственно. … 19 мая '
  '2022 года — СОФТВЭРУАН АГ вышел из состава участников доля 100.0%. 19 мая 2022 года — Ермаков Александр '
  'Владимирович вошел в состав участников доля 60.0%. 19 мая 2022 года — Шумаков Юрий Алексеевич вошел в состав '
  'участников доля 40.0%. … ООО «ВАН АЙ ТИ ТРЕЙД», ИНН 5044057860 … Awara IT в России станет частью этой российской '
  'структуры (бренд WONE IT).',
  'https://www.comnews.ru/content/220241/2022-05-17/2022-w20/awara-it-poglotila-aktivy-softwareone-rossii'),
 ('gfc7e5649',
  'eco.rationale',
  'Швейцарская SoftwareONE продала российский бизнес по лицензированию программного обеспечения компании Awara IT '
  'Group в рамках ухода с российского рынка.',
  'Швейцарская SoftwareONE уходила из России.',
  'SoftwareONE AG приняла решение об уходе с российского рынка.',
  'https://www.comnews.ru/content/220241/2022-05-17/2022-w20/awara-it-poglotila-aktivy-softwareone-rossii'),
 ('gfc7e5649',
  'law.terms',
  'В Awara IT ответили, что не разглашают сумму сделки.',
  '—',
  'Российские частные инвесторы, совладельцы компании-интегратора Awara IT Group Александр Ермаков и Юрий Шумаков '
  'купили ООО "СофтварэУАН" (SoftwareONE Russia). Доли партнеров распределены как 60% и 40% соответственно.',
  'https://www.comnews.ru/content/220241/2022-05-17/2022-w20/awara-it-poglotila-aktivy-softwareone-rossii'),
 ('gfc7e5649',
  'eco.target_fin',
  'Выручка «СофтвэрУАН» за 2020 год — без малого 9,59 млрд ₽, за 2021-й — около 9,47 млрд ₽. Это ООО, которым '
  'SoftwareONE владела целиком; общество зарегистрировано в феврале 2007 г. и успело сменить несколько названий — '
  '«Общество информационных технологий», «ПС-Вэйр», а с 2012 г. «Компарекс».',
  'Выручка ООО «СофтвэрУАН» — около 9,59 млрд ₽ в 2020 году и около 9,47 млрд ₽ в 2021 году.',
  'Выручка ООО "СофтвэрУАН", по данным kartoteka.ru, в 2021 г. составила почти 9,47 млрд руб., а в 2020 г. - без '
  'малого 9,59 млрд руб.',
  'https://www.comnews.ru/content/220241/2022-05-17/2022-w20/awara-it-poglotila-aktivy-softwareone-rossii'),
 ('gfc7e5649',
  'eco.context',
  'После сделки появилась совместная мультивендорная ИТ-компания полного цикла под брендом WONE IT — сейчас она '
  'работает как ООО «Ван Ай Ти Трейд» под брендом Wone IT. Доли собственников с тех пор не изменились: 60% у '
  'Александра Ермакова, 40% у Юрия Шумакова.',
  'SoftwareONE работала в России через ООО «СофтвэрУАН», созданное в 2007 году (прежние названия — «Общество '
  'информационных технологий», «ПС-Вэйр», с 2012 года — «Компарекс»). Группа Awara IT по выручке была в 18,6 раза '
  'меньше купленной компании: 507 млн ₽ против 9,47 млрд ₽ за 2021 год.\n'
  '\n'
  'Гендиректором объединенной компании стал Юрий Шумаков, в ней рассчитывали на более чем 400 сотрудников. Доли '
  'владельцев с тех пор не менялись: 60% у Александра Ермакова, 40% у Юрия Шумакова.',
  'В России SoftwareONE действовала через 100%-ную "дочку" - ООО "СофтвэрУАН", созданную в феврале 2007 г. (тогда '
  'компания называлась ООО "Общество информационных технологий", затем - ООО "ПС-Вэйр", а с 2012 г. - ООО '
  '"Компарекс"). … Примечательно, что выручка покупателя - компаний группы Awara IT - в 18,6 раз меньше выручки '
  'купленного ООО "СофтвэрУАН" - 507 млн руб. против 9,47 млрд руб. по итогам 2021г. … "Генеральным директором '
  'компании становится Юрий Шумаков, в настоящий момент он также руководит компанией "Авара Ай Ти Солюшенс". Общая '
  'численность сотрудников компании составит более 400 человек. … 19 мая 2022 года — СОФТВЭРУАН АГ вышел из состава '
  'участников доля 100.0%. 19 мая 2022 года — Ермаков Александр Владимирович вошел в состав участников доля 60.0%. '
  '19 мая 2022 года — Шумаков Юрий Алексеевич вошел в состав участников доля 40.0%.',
  'https://www.comnews.ru/content/220241/2022-05-17/2022-w20/awara-it-poglotila-aktivy-softwareone-rossii'),
 ('gfc7e5649',
  'extra',
  'Швейцарская SoftwareONE продала российский бизнес по лицензированию программного обеспечения компании Awara IT '
  'Group, уходя с российского рынка. Сделка учтена в проекте KSE Institute «Leave Russia» и по возможности сверена с '
  'независимой прессой.',
  'Российский бизнес SoftwareONE купила не компания Awara IT, а ее совладельцы; объединенный бизнес работает под '
  'брендом WONE IT.',
  'Российские частные инвесторы, совладельцы компании-интегратора Awara IT Group Александр Ермаков и Юрий Шумаков '
  'купили ООО "СофтварэУАН" (SoftwareONE Russia). Доли партнеров распределены как 60% и 40% соответственно. … Awara '
  'IT в России станет частью этой российской структуры (бренд WONE IT).',
  'https://www.comnews.ru/content/220241/2022-05-17/2022-w20/awara-it-poglotila-aktivy-softwareone-rossii'),
 ('gc677124b',
  'title',
  'Aggreko продала евразийский бизнес по аренде энергооборудования «Бурсервису»',
  '«БурСервис» купил «Аггреко Евразия» у Aggreko',
  'АО «БурСервис» сообщает о завершении сделки по приобретению ООО «Аггреко Евразия»',
  'https://www.burservis.ru/news/20-11-25'),
 ('gc677124b',
  'date',
  '2025-11-20',
  '2025-11-19',
  '19 ноября 2025 года — КОМПАНИЯ С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ АГГРЕКО ХОЛДИНГЗ ЛИМИТЕД вышел из состава '
  'участников доля 99.0%. 19 ноября 2025 года — АО "БУРСЕРВИС" вошел в состав участников доля 100.0%.',
  'https://projectcompass.ru/api/companies/g69b9ab00/fns'),
 ('gc677124b',
  'sum',
  '$29 млн',
  '$21 млн',
  'Aggreko reported that the sales price comprised $21 million for the Russian segment and $8 million for '
  'Kazakhstan. Albion JVCo, Aggreko’s owner, said it would take an $82 million impairment charge on the sale once '
  'completed. The Russian business reported revenues of $106 million for the year ending December 28, 2024',
  'https://www.internationalrentalnews.com/news/russia-/8062061.article'),
 ('gc677124b',
  'eco.sum',
  '$29 млн',
  '$21 млн',
  'Aggreko reported that the sales price comprised $21 million for the Russian segment and $8 million for '
  'Kazakhstan. Albion JVCo, Aggreko’s owner, said it would take an $82 million impairment charge on the sale once '
  'completed. The Russian business reported revenues of $106 million for the year ending December 28, 2024',
  'https://www.internationalrentalnews.com/news/russia-/8062061.article'),
 ('gc677124b',
  'eco.share',
  'Распоряжением разрешено приобретение 99% ООО «Аггреко Евразия», принадлежащих Aggreko Holdings Limited, и 1%, '
  'принадлежащего Aggreko UK Limited.',
  '100% долей ООО «Аггреко Евразия»: 99% у Aggreko Holdings Limited, 1% у Aggreko UK Limited',
  'разрешить совершение акционерным обществом "БурСервис" сделок по приобретению 99 процентов долей в уставном '
  'капитале общества с ограниченной ответственностью "Аггреко Евразия", принадлежащих Аггреко Холдингз Лимитед '
  '(Aggreko Holdings Limited), и 1 процента долей в уставном капитале указанного общества, принадлежащего Аггреко '
  'ЮКей Лимитед (Aggreko UK Limited). 2. Для совершения сделок, указанных в настоящем распоряжении, не требуется '
  'получение иных предусмотренных законодательством Российской Федерации разрешений',
  'http://www.kremlin.ru/acts/bank/51958/print'),
 ('gc677124b',
  'eco.val',
  '—',
  'В апреле 2025 года Aggreko сообщила, что продает бизнес в Евразии неназванному покупателю за $29 млн: $21 млн за '
  'российскую часть и $8 млн за казахстанскую. Владелец Aggreko, Albion JVCo, ожидал после закрытия сделки списания '
  '$82 млн.',
  'Aggreko announced in April that it had agreed to sell its Eurasian power rental businesses —including Russian and '
  'Kazakhstan operations—for US$29 million to an unnamed buyer, subject to Russian government approval. … Aggreko '
  'reported that the sales price comprised $21 million for the Russian segment and $8 million for Kazakhstan. Albion '
  'JVCo, Aggreko’s owner, said it would take an $82 million impairment charge on the sale once completed. The '
  'Russian business reported revenues of $106 million for the year ending December 28, 2024 … Распоряжение '
  'Президента Российской Федерации от 26.05.2025 г. № 196-рп',
  'https://www.internationalrentalnews.com/news/russia-/8062061.article'),
 ('gc677124b',
  'eco.target_fin',
  'По итогам 2024 года выручка «Аггреко Евразия» составила почти 10 млрд ₽, чистая прибыль — 2,43 млрд ₽.',
  'По итогам 2024 года выручка ООО «Аггреко Евразия» превысила 9,9 млрд ₽, чистая прибыль — 2,43 млрд ₽. Aggreko '
  'оценивала выручку российского бизнеса за 2024 год в $106 млн.',
  'В 2024 году выручка компании превысила 9,9 млрд рублей, чистая прибыль составила 2,43 млрд рублей. … Aggreko '
  'reported that the sales price comprised $21 million for the Russian segment and $8 million for Kazakhstan. Albion '
  'JVCo, Aggreko’s owner, said it would take an $82 million impairment charge on the sale once completed. The '
  'Russian business reported revenues of $106 million for the year ending December 28, 2024',
  'https://www.interfax.ru/russia/1027809'),
 ('gc677124b',
  'law.appr',
  'Президент России Владимир Путин подписал распоряжение о специальном решении о совершении сделок АО «БурСервис». '
  'Документ опубликован на портале правовых актов.',
  'Сделку разрешил президент России распоряжением № 196-рп от 26 мая 2025 года; других разрешений и согласований для '
  'нее не требовалось.',
  'Распоряжение Президента Российской Федерации от 26.05.2025 г. № 196-рп … разрешить совершение акционерным '
  'обществом "БурСервис" сделок по приобретению 99 процентов долей в уставном капитале общества с ограниченной '
  'ответственностью "Аггреко Евразия", принадлежащих Аггреко Холдингз Лимитед (Aggreko Holdings Limited), и 1 '
  'процента долей в уставном капитале указанного общества, принадлежащего Аггреко ЮКей Лимитед (Aggreko UK Limited). '
  '2. Для совершения сделок, указанных в настоящем распоряжении, не требуется получение иных предусмотренных '
  'законодательством Российской Федерации разрешений',
  'http://www.kremlin.ru/acts/bank/51958/print'),
 ('gc677124b',
  'law.terms',
  'Других разрешений, согласий и согласований по законам РФ, в том числе предварительных, для сделок из распоряжения '
  'не нужно.',
  '—',
  'разрешить совершение акционерным обществом "БурСервис" сделок по приобретению 99 процентов долей в уставном '
  'капитале общества с ограниченной ответственностью "Аггреко Евразия", принадлежащих Аггреко Холдингз Лимитед '
  '(Aggreko Holdings Limited), и 1 процента долей в уставном капитале указанного общества, принадлежащего Аггреко '
  'ЮКей Лимитед (Aggreko UK Limited). 2. Для совершения сделок, указанных в настоящем распоряжении, не требуется '
  'получение иных предусмотренных законодательством Российской Федерации разрешений',
  'http://www.kremlin.ru/acts/bank/51958/print'),
 ('gc677124b',
  'eco.context',
  'В 2022 году Halliburton завершила продажу российского подразделения российской управленческой команде из бывших '
  'сотрудников Halliburton и больше не ведет операции в России. Команда менеджеров стала владеть бывшим бизнесом и '
  'активами Halliburton в России под названием «БурСервис», независимым от Halliburton. «БурСервис» продолжил '
  'консолидацию нефтесервисного рынка: в феврале 2026 года (запись в ЕГРЮЛ от 13 февраля) компания стала владельцем '
  '51% производителя нефтегазового оборудования «Уфабурмаш». По оценке консультантов, эта сделка снижает зависимость '
  'группы от зарубежных поставщиков бурового инструмента в условиях санкций. В 2024 году выручка самого «БурСервиса» '
  'выросла на 21,1%, до 47,86 млрд ₽, чистая прибыль — на 17%, до 14 млрд ₽.',
  'Еще в марте 2022 года Aggreko решила продать российский бизнес; до продажи он работал отдельно от остальной '
  'группы, и инвестиции в него прекратились. «Аггреко Евразия» работает в СНГ с 2008 года: обеспечивает мобильное '
  'энергоснабжение и температурный контроль нефтегазовых, цементных, стекольных и горнорудных предприятий.\n'
  '\n'
  'Покупатель, «БурСервис», — нефтесервисная компания, преемник российских активов Halliburton. Покупка «Аггреко '
  'Евразия» — его вторая сделка M&A в 2025 году.',
  'Британская Aggreko объявила о намерении продать этот бизнес, который в основном сосредоточен в России, еще в '
  'марте 2022-го. Компания управляла этим активом отдельно от остальной части Aggreko для поддержки сотрудников, '
  'прекратив при этом инвестиции в развитие проекта. … "Аггреко Евразия" работает на территории СНГ с 2008 года, '
  'предоставляет комплексные услуги по обеспечению гибкого мобильного энергоснабжения и температурному контролю для '
  'строящихся и действующих предприятий в различных секторах экономики: нефтегазовой, цементной, стекольной, '
  'горнорудной и других отраслях. … "БурСервис" - один из крупнейших нефтесервисных подрядчиков России, ставший '
  'преемником российских активов Halliburton. … является второй сделкой слияний и поглощений АО «БурСервис», '
  'реализованной в 2025 г.',
  'https://www.interfax.ru/russia/1027809'),
 ('gc677124b',
  'extra',
  'Британская Aggreko UK продала бизнес по аренде энергооборудования в Евразии (Россия и сопредельные страны) '
  'компании «Бурсервис» за $29 млн. Сделка учтена в трекере ухода иностранных компаний KSE Institute «Leave Russia».',
  '«БурСервис», преемник российских активов Halliburton, купил российский бизнес британской Aggreko по мобильному '
  'энергоснабжению; Aggreko искала покупателя три года.',
  '"БурСервис" - один из крупнейших нефтесервисных подрядчиков России, ставший преемником российских активов '
  'Halliburton. … "Аггреко Евразия" работает на территории СНГ с 2008 года, предоставляет комплексные услуги по '
  'обеспечению гибкого мобильного энергоснабжения и температурному контролю для строящихся и действующих предприятий '
  'в различных секторах экономики: нефтегазовой, цементной, стекольной, горнорудной и других отраслях. … The sale '
  'follows a three-year effort by Aggreko to divest these assets',
  'https://www.interfax.ru/russia/1027809'),
 ('g94683ed2',
  'seller',
  'Акционеры Рив Гош',
  'Rive Gauche Group Ltd',
  'Эти компании занимаются развитием парфюмерной сети «Рив Гош» и ранее контролировались кипрской структурой Rive '
  'Gauche Group Ltd. … 15 декабря 2025 года — КОМПАНИЯ "РИВ ГОШ ГРУП (КИПР) ЛИМИТЕД" вышел из состава участников '
  'доля 100.0%. 15 декабря 2025 года — ООО "РВБ" вошел в состав участников доля 100.0%.',
  'https://www.kommersant.ru/doc/8292342'),
 ('g94683ed2',
  'title',
  'Wildberries & Russ приобрела сеть «Рив Гош»',
  'Wildberries & Russ купил сеть «Рив Гош»',
  'Wildberries-Russ (ООО "РВБ") стала владельцем юрлиц парфюмерной сети "Рив Гош". По данным ЕГРЮЛ, сделка '
  'состоялась 15 декабря. "РВБ" получило 100% ООО "Аромалюкс" и ООО "УК ПС Групп", владельцами которых ранее была '
  'кипрская Rive Gauche Group Ltd.',
  'https://www.interfax.ru/business/1063390'),
 ('g94683ed2',
  'sum',
  'Не раскрыта',
  '5–6 млрд ₽ (по оценке)',
  'Стоимость сделки могла составить 5–6 млрд руб.',
  'https://www.kommersant.ru/doc/8292342'),
 ('g94683ed2',
  'eco.sum',
  'Не раскрыта',
  '5–6 млрд ₽ (по оценке)',
  'Стоимость сделки могла составить 5–6 млрд руб.',
  'https://www.kommersant.ru/doc/8292342'),
 ('g94683ed2',
  'eco.share',
  'Сейчас у сети более 250 магазинов в 88 городах.',
  '100% долей ООО «Аромалюкс» и ООО «УК ПС Групп»',
  'Wildberries-Russ (ООО "РВБ") стала владельцем юрлиц парфюмерной сети "Рив Гош". По данным ЕГРЮЛ, сделка '
  'состоялась 15 декабря. "РВБ" получило 100% ООО "Аромалюкс" и ООО "УК ПС Групп", владельцами которых ранее была '
  'кипрская Rive Gauche Group Ltd.',
  'https://www.interfax.ru/business/1063390'),
 ('g94683ed2',
  'eco.val',
  'Бурмистров оценивает сделку с учетом долга в 5–6 млрд ₽. Весь бизнес компании, по его оценке, стоит свыше 12 млрд '
  '₽.',
  'Гендиректор «Infoline-Аналитики» Михаил Бурмистров оценивает сделку с учетом долга в 5–6 млрд ₽, а весь бизнес '
  '«Рив Гош» — более чем в 12 млрд ₽. Стороны сумму не называли.',
  'Гендиректор «Infoline-Аналитики» Михаил Бурмистров полагает, что стоимость сделки с учетом долга составила 5–6 '
  'млрд руб. Весь бизнес компании стоит более 12 млрд руб., говорит он. … Стоимость сделки могла составить 5–6 млрд '
  'руб.',
  'https://www.kommersant.ru/doc/8292342'),
 ('g94683ed2',
  'eco.target_fin',
  'У «УК ПС Групп» в 2024 году выручка составила 1,36 млрд ₽, чистая прибыль — 2,98 млн ₽. Прибыль за год выросла в '
  'пять раз, выручка — на 3,4%.',
  'Выручка ООО «Аромалюкс», операционной компании сети, за 2024 год снизилась на 6%, до 37,4 млрд ₽, чистый убыток '
  'вырос почти втрое, до 1,5 млрд ₽. У ООО «УК ПС Групп» выручка за 2024 год — 1,36 млрд ₽ (+3,4%), чистая прибыль — '
  '2,98 млн ₽, в пять раз больше, чем годом ранее.',
  'Выручка «Аромалюкса» в 2024 году, по данным СПАРК, снизилась на 6% год к году, до 37,4 млрд руб. Чистый убыток '
  'увеличился почти в три раза, до 1,5 млрд руб. Выручка «УК ПС Групп» в 2024 году составила 1,36 млрд руб., чистая '
  'прибыль — 2,98 млн руб. Год к году значения выросли на 3,4% и в пять раз соответственно.',
  'https://www.kommersant.ru/doc/8292342'),
 ('g94683ed2',
  'eco.context',
  '26 сентября Wildberries и «Рив Гош» объявили о стратегическом партнерстве. По его условиям магазины сети стали '
  'пунктами самовывоза заказов Wildberries, а сама «Рив Гош» получила отдельный раздел в каталоге парфюмерии и '
  'косметики маркетплейса.',
  '«Рив Гош» основали в 1995 году Павел и Лариса Карабань. Сеть продает в основном премиальную парфюмерию и '
  'косметику, у нее более 250 магазинов в 88 городах; по данным Infoline, это пятый по обороту '
  'парфюмерно-косметический ритейлер России. На 2021 год 51% кипрской Rive Gauche Group Ltd принадлежал Инне Мейер, '
  '25% — у панамской Octapan Investments (ее бенефициарами называют основателей сети), 24% — у Lenka Investments, '
  'которую связывали с Олегом Бойко.\n'
  '\n'
  'Покупку сети раньше обсуждала «Севергрупп» Алексея Мордашова. 26 сентября 2025 года Wildberries и «Рив Гош» '
  'объявили о партнерстве: 252 магазина сети стали пунктами выдачи заказов маркетплейса, а сеть получила свой раздел '
  'в каталоге Wildberries.',
  '«Рив Гош» основана в 1995 году бывшими супругами Павлом и Ларисой Карабань. Сеть специализируется на продаже '
  'парфюмерии и косметики, преимущественно премиальной, дороже 4 тыс. руб. за упаковку. Сейчас у нее более 250 '
  'магазинов в 88 городах России. Согласно Infoline, «Рив Гош» пятый по обороту парфюмерно-косметический ритейлер '
  'России. … На 2021 год ее основным владельцем была Инна Мейер (51%), жена Августа Мейера, бывшего совладельца сети '
  '«Юлмарт». … Еще 25% Rive Gauche Group Ltd. ранее были на балансе панамской Octapan Investments S.A., '
  'бенефициарами которой считаются Павел и Лариса Карабань. 24% контролировала Lenka Investments Ltd, ранее '
  'связанная с основателем Finstar Financial Group Олегом Бойко. … Ранее переговоры о покупке «Рив Гош» велись к '
  '«Севергрупп» Алексея Мордашова. … 26 сентября Wildberries и "Рив Гош" объявили о стратегическом партнерстве … В '
  'нем компании объявили о стратегическом партнерстве: 252 магазина торговой сети подключились к сервису '
  'маркетплейса по самовывозу товаров. Взамен ритейлер получил собственный раздел в каталоге Wildberries. … 15 '
  'декабря 2025 г. Сделка закрыта 15 декабря.',
  'https://www.kommersant.ru/doc/8077406'),
 ('g94683ed2',
  'law.terms',
  'Дополнительно в залог ООО «РВБ» получило 100% долей ООО «Аромалюкс» и его дочернего ООО «Ароматех».',
  'В октябре 2025 года, до перехода долей, ООО «РВБ» получило в залог 100% ООО «Аромалюкс» и его дочернего ООО '
  '«Ароматех».',
  'Кроме того, ООО "РВБ" получило в залог 100%-ю долю в ООО "Аромалюкс" и его "дочке" ООО "Ароматех". … В октябре '
  'РВБ получила 100% «Аромалюкса» в залог. … 15 декабря 2025 г. Сделка закрыта 15 декабря.',
  'https://www.interfax.ru/business/1063390'),
 ('g94683ed2',
  'extra',
  'Юридическая фирма «Дякин, Горцунян и Партнеры» выступила советником акционеров «Рив Гош». '
  'Инвестиционно-банковская группа Aspring Capital также консультировала продающих акционеров.',
  'Wildberries & Russ сначала подключил магазины «Рив Гош» к выдаче заказов, затем взял в залог операционную '
  'компанию сети и через три месяца после объявления о партнерстве стал ее владельцем.',
  '26 сентября Wildberries и "Рив Гош" объявили о стратегическом партнерстве … Кроме того, ООО "РВБ" получило в '
  'залог 100%-ю долю в ООО "Аромалюкс" и его "дочке" ООО "Ароматех". … Wildberries-Russ (ООО "РВБ") стала владельцем '
  'юрлиц парфюмерной сети "Рив Гош". По данным ЕГРЮЛ, сделка состоялась 15 декабря. "РВБ" получило 100% ООО '
  '"Аромалюкс" и ООО "УК ПС Групп", владельцами которых ранее была кипрская Rive Gauche Group Ltd.',
  'https://www.interfax.ru/business/1063390'),
 ('ga0a49202',
  'buyer',
  'g6eb3c726',
  None,
  'В конце июня 2025 года были учреждены два новых юрлица: ООО «Клаустрофобия Онлайн» и ООО «Клаустрофобия Офлайн». '
  'В обоих юрлицах 51% принадлежит инвестору в бизнес квестов Вадиму Змовику, 33% — инвестору GrimTeam Павлу '
  'Вараксину и 16% — сооснователю GrimTeam Евгению Авину … В рамках сделки новым юрлицам перешли товарные знаки, '
  'утверждает Вараксин.',
  'https://www.rbc.ru/technology_and_media/15/08/2025/689db55a9a7947b058474799'),
 ('ga0a49202',
  'buyer_name',
  None,
  'ООО «Клаустрофобия Офлайн» и ООО «Клаустрофобия Онлайн» (Вадим Змовик, Павел Вараксин, Евгений Авин)',
  'В конце июня 2025 года были учреждены два новых юрлица: ООО «Клаустрофобия Онлайн» и ООО «Клаустрофобия Офлайн». '
  'В обоих юрлицах 51% принадлежит инвестору в бизнес квестов Вадиму Змовику, 33% — инвестору GrimTeam Павлу '
  'Вараксину и 16% — сооснователю GrimTeam Евгению Авину … В рамках сделки новым юрлицам перешли товарные знаки, '
  'утверждает Вараксин.',
  'https://www.rbc.ru/technology_and_media/15/08/2025/689db55a9a7947b058474799'),
 ('ga0a49202',
  'title',
  'GrimTeam приобрел сеть квестов «Клаустрофобия»',
  'Вадим Змовик и основатели GrimTeam купили сеть квестов «Клаустрофобия»',
  'В конце июня 2025 года были учреждены два новых юрлица: ООО «Клаустрофобия Онлайн» и ООО «Клаустрофобия Офлайн». '
  'В обоих юрлицах 51% принадлежит инвестору в бизнес квестов Вадиму Змовику, 33% — инвестору GrimTeam Павлу '
  'Вараксину и 16% — сооснователю GrimTeam Евгению Авину … Владельцами сети квестов «Клаустрофобия» стали основатели '
  'ее конкурента — GrimTeam.',
  'https://www.rbc.ru/technology_and_media/15/08/2025/689db55a9a7947b058474799'),
 ('ga0a49202',
  'date',
  '2025-07-01',
  '2025-08-01',
  'Владимир Жиганов в разговоре с РБК уточнил, что передача активов состоялась 1 августа.',
  'https://www.rbc.ru/technology_and_media/15/08/2025/689db55a9a7947b058474799'),
 ('ga0a49202',
  'sum',
  '400 млн ₽',
  '400 млн ₽ (по оценке)',
  'Аналитики тогда оценили компанию в 400 млн руб. Сделка, по словам Вараксина, прорабатывалась около полугода и '
  'прошла «в пределах озвученной ранее суммы».',
  'https://www.rbc.ru/technology_and_media/15/08/2025/689db55a9a7947b058474799'),
 ('ga0a49202',
  'eco.sum',
  '400 млн ₽',
  '400 млн ₽ (по оценке)',
  'Аналитики тогда оценили компанию в 400 млн руб. Сделка, по словам Вараксина, прорабатывалась около полугода и '
  'прошла «в пределах озвученной ранее суммы».',
  'https://www.rbc.ru/technology_and_media/15/08/2025/689db55a9a7947b058474799'),
 ('ga0a49202',
  'eco.share',
  'Покупатели — новые ООО «Клаустрофобия онлайн» и «Клаустрофобия офлайн»: в каждом 51% у Вадима Змовика, 33% у '
  'Павла Вараксина (GrimTeam), 16% у Евгения Авина.',
  'Активы сети «Клаустрофобия»: товарные знаки, сайт, соцсети, программы и права аренды площадок вместе с '
  'оборудованием',
  'В рамках сделки новым юрлицам перешли товарные знаки, утверждает Вараксин. … Также произошла переуступка прав '
  'аренды на локации и их оборудование, приобретение прав на программное обеспечение и социальные сети '
  '«Клаустрофобии». Домен «клаустрофобия.рф» — основной сайт сети — также переоформлен на одно из новых юрлиц',
  'https://www.rbc.ru/technology_and_media/15/08/2025/689db55a9a7947b058474799'),
 ('ga0a49202',
  'law.adv',
  [['Стороны сделки', 'Не раскрывались', 'Юридические консультанты в публичных источниках не раскрывались']],
  [],
  'В конце июня 2025 года были учреждены два новых юрлица: ООО «Клаустрофобия Онлайн» и ООО «Клаустрофобия Офлайн». '
  'В обоих юрлицах 51% принадлежит инвестору в бизнес квестов Вадиму Змовику, 33% — инвестору GrimTeam Павлу '
  'Вараксину и 16% — сооснователю GrimTeam Евгению Авину',
  'https://www.rbc.ru/technology_and_media/15/08/2025/689db55a9a7947b058474799'),
 ('ga0a49202',
  'eco.val',
  'По экспертной оценке, сеть стоит 400–500 млн ₽.',
  'В августе 2024 года гендиректор «INFOLine-Аналитики» Михаил Бурмистров оценил бизнес «Клаустрофобии» не меньше '
  'чем в 400 млн ₽, по неофициальным данным — в 400–500 млн ₽. По словам Павла Вараксина, сделка прошла в пределах '
  'этой суммы.',
  'Бизнес «Клаустрофобии», по самым консервативным оценкам, может стоить не менее 400 млн руб., считает Бурмистров. '
  '… Сам бизнес «Клаустрофобии», продолжает источник, тогда был оценен в 400–500 млн руб. … считает гендиректор '
  '«INFOLine-Аналитики» Михаил Бурмистров … Аналитики тогда оценили компанию в 400 млн руб. Сделка, по словам '
  'Вараксина, прорабатывалась около полугода и прошла «в пределах озвученной ранее суммы». … Еще в августе 2024 года '
  'стало известно о том, что «Клаустрофобия» ищет покупателя бизнеса. Источники говорили, что в 2023 году шли '
  'переговоры о продаже бизнеса «МТС Энтертеймент» (сейчас компания называется МТС Live), но стороны не сошлись по '
  'цене и сути сделки.',
  'https://www.rbc.ru/technology_and_media/27/08/2024/66cc760e9a794719ed48a5bd'),
 ('ga0a49202',
  'law.terms',
  'По словам Павла Вараксина, в новой команде останутся все сотрудники, стоявшие у истоков сети. Владимир Жиганов и '
  'его менеджмент покинут проекты.',
  'По словам Павла Вараксина, в сети останутся ключевые сотрудники, которые работали в ней с самого начала, а бывший '
  'управляющий Владимир Жиганов и его менеджмент уйдут.',
  'В команде «Клаустрофобии», по словам Вараксина, останутся все ключевые сотрудники, «которые были у истоков '
  'создания сети» до прихода команды управляющих Владимира Жиганова. Сам Жиганов, как утверждает Вараксин, и его '
  'менеджмент покинут проекты.',
  'https://www.rbc.ru/technology_and_media/15/08/2025/689db55a9a7947b058474799'),
 ('ga0a49202',
  'eco.context',
  'Сделка обсуждалась около полугода. Еще в августе 2024 года стало известно, что «Клаустрофобия» ищет покупателя '
  'бизнеса. По неофициальным данным, в 2023 году шли переговоры о продаже бизнеса «МТС Энтертеймент» (сейчас '
  'компания называется МТС Live), но стороны не сошлись по цене и сути сделки. «Клаустрофобия» основана в 2013 году '
  'Богданом Кравцовым, Тимуром Кадыровым и Сергеем Кузнецовым. В 2019 году ее приобрел Ручьев за 80 млн ₽.',
  'Сеть создали в 2013 году Богдан Кравцов, Тимур Кадыров и Сергей Кузнецов. Александр Ручьев, президент ГК «Основа» '
  'и бывший владелец застройщика «Мортон», купил ее в 2019 году, когда бизнес продавали с оценкой 80 млн ₽. До '
  'сделки сеть принадлежала двум юрлицам — ООО «Клаустрофобия — В» и ООО «Серьезные игры»; в 2024 году у нее было 37 '
  'точек и 169 активных квестов.\n'
  '\n'
  'Покупателя сеть искала с августа 2024 года. По неофициальным данным, в 2023 году ее пытались продать «МТС '
  'Энтертеймент» (теперь МТС Live), но стороны не договорились о цене и условиях.',
  'Сеть квестов «Клаустрофобия» была основана в 2013 году Богданом Кравцовым, Тимуром Кадыровым и Сергеем '
  'Кузнецовым. В 2019 году бизнес был выставлен на продажу с оценкой 80 млн руб. Тогда компанию купил президент ГК '
  '«Основа», экс-владелец одного из крупнейших в России застройщиков «Мортон» Александр Ручьев. Прежде сеть была '
  'представлена двумя юрлицами — ООО «Клаустрофобия — В» и «ООО «Серьезные игры». … По состоянию на 2024 год сеть '
  'управляет 37 точками и насчитывает 169 активных квестов. … Еще в августе 2024 года стало известно о том, что '
  '«Клаустрофобия» ищет покупателя бизнеса. Источники говорили, что в 2023 году шли переговоры о продаже бизнеса '
  '«МТС Энтертеймент» (сейчас компания называется МТС Live), но стороны не сошлись по цене и сути сделки.',
  'https://www.rbc.ru/technology_and_media/15/08/2025/689db55a9a7947b058474799'),
 ('ga0a49202',
  'extra',
  'Сделка включала приобретение до 100% бизнеса сети «Клаустрофобия», в том числе товарных знаков, прав на '
  'программное обеспечение и социальные сети, а также переуступку прав аренды на 37 локаций и их оборудование. Сеть '
  'насчитывает 169 активных квестов, ее оборот — около 1–1,1 млрд ₽. Новые владельцы планируют запускать совместные '
  'проекты с российскими стриминговыми сервисами, развлекательными компаниями и блогерами, а также возрождать '
  'популярные квесты сети. Сеть квестов «Клаустрофобия» перешла от прежнего владельца — президента ГК «Основа» '
  'Александра Ручьева, владевшего сетью с 2019 года — команде конкурирующей сети GrimTeam: 1 августа 2025 года '
  'учреждены два юрлица, «Клаустрофобия онлайн» и «Клаустрофобия офлайн», где 51% принадлежит инвестору Вадиму '
  'Змовику, 33% — сооснователю GrimTeam Павлу Вараксину и 16% — Евгению Авину, назначенному генеральным директором. '
  'Ранее рассматривалась продажа МТС Live и Яндексу, но переговоры с МТС в итоге не привели к сделке — стороны не '
  'сошлись в цене и условиях.',
  'Сделку оформили покупкой активов, а не долей: новым компаниям перешли бренды, домен, соцсети, программы и аренда '
  'площадок с оборудованием. По словам Павла Вараксина, новые владельцы планируют совместные проекты со '
  'стриминговыми сервисами, развлекательными компаниями и блогерами и хотят вернуть культовые квесты сети.',
  'В рамках сделки новым юрлицам перешли товарные знаки, утверждает Вараксин. … Также произошла переуступка прав '
  'аренды на локации и их оборудование, приобретение прав на программное обеспечение и социальные сети '
  '«Клаустрофобии». Домен «клаустрофобия.рф» — основной сайт сети — также переоформлен на одно из новых юрлиц … '
  'Новая команда, по словам Вараксина, планирует создавать как новые совместные проекты, в том числе с участием '
  'российских стриминговых сервисов, компаний из сферы развлечений и блогеров, так и «возрождать культовые проекты '
  '«Клаустрофобии».',
  'https://www.rbc.ru/technology_and_media/15/08/2025/689db55a9a7947b058474799'),
 ('gd88cbe9a',
  'title',
  'Highland Gold купила ООО «Гейзер Голд» с лицензиями на месторождения золота и серебра на Камчатке',
  'Highland Gold купил «Гейзер Голд» с лицензиями на Камчатке',
  'Структура «Хайлэнд Голд» Владислава Свиблова 3 июня стала владельцем компании «Гейзер Голд» с лицензиями на '
  'геологическое изучение месторождений золота и серебра на Камчатке, следует из данных ЕГРЮЛ и Роснедр. Прежним '
  'собственником «Гейзер Голд» было ООО «Гиперспэйс», основанное бывшим совладельцем Челябинского трубопрокатного '
  'завода (ЧТПЗ) Андреем Комаровым',
  'https://www.kommersant.ru/doc/7796300'),
 ('gd88cbe9a',
  'law.adv',
  [['Стороны сделки', 'Не раскрывались', 'Юридические консультанты в публичных источниках не раскрывались']],
  [],
  'Структура «Хайлэнд Голд» Владислава Свиблова 3 июня стала владельцем компании «Гейзер Голд» с лицензиями на '
  'геологическое изучение месторождений золота и серебра на Камчатке, следует из данных ЕГРЮЛ и Роснедр. Прежним '
  'собственником «Гейзер Голд» было ООО «Гиперспэйс», основанное бывшим совладельцем Челябинского трубопрокатного '
  'завода (ЧТПЗ) Андреем Комаровым',
  'https://www.kommersant.ru/doc/7796300'),
 ('gd88cbe9a',
  'eco.rationale',
  'Highland Gold хочет усилить позиции в стратегически важном регионе — на участке Охотско-Чукотского пояса, где '
  'есть золото.',
  'По мнению независимого эксперта Леонида Хазанова, «Хайлэнд Голд» рассчитывает найти на участках значительные '
  'запасы, а для разведки у компании есть опытные геологи и оборудование. В самой компании от комментариев '
  'отказались.',
  '«Хайлэнд Голд», вероятно, видит потенциал обнаружения приличных запасов, к тому же у компании есть опытные '
  'геологи и необходимое оборудование, добавляет независимый эксперт Леонид Хазанов. … Сейчас собственник 99,9% '
  '«Гиперспэйс» в ЕГРЮЛ скрыт, 0,1% принадлежит самой компании. В Highland Gold отказались от комментариев.',
  'https://www.kommersant.ru/doc/7796300'),
 ('gd88cbe9a',
  'extra',
  'Highland Gold приобрела 100% долей ООО «Гейзер Голд» с лицензиями на геологическое изучение месторождений золота '
  'и серебра на участках недр «Кларин» и «Нимаевский» в Усть-Камчатском районе. Продавец — Андрей Комаров '
  '(экс-владелец ЧТПЗ). Участки находятся на ранней стадии поисково-оценочных работ и принадлежат золотоносному '
  'Охотско-Чукотскому поясу. Прогнозные затраты на геологическое изучение — 100–250 млн ₽.',
  'Highland Gold купила у ООО «Гиперспэйс», основанного бывшим совладельцем ЧТПЗ Андреем Комаровым, компанию с двумя '
  'лицензиями на поиск золота и серебра на Камчатке. Участки на ранней стадии изучения: по оценке независимого '
  'эксперта Максима Худалова, геологическое изучение стоит 100–250 млн ₽, а на Камчатке может обойтись вдвое дороже '
  'из-за нехватки техники и персонала.',
  'Структура «Хайлэнд Голд» Владислава Свиблова 3 июня стала владельцем компании «Гейзер Голд» с лицензиями на '
  'геологическое изучение месторождений золота и серебра на Камчатке, следует из данных ЕГРЮЛ и Роснедр. Прежним '
  'собственником «Гейзер Голд» было ООО «Гиперспэйс», основанное бывшим совладельцем Челябинского трубопрокатного '
  'завода (ЧТПЗ) Андреем Комаровым … Старший менеджер «S+ Консалтинг» Дмитрий Гомер говорит, что участки находятся '
  'на ранней стадии поисково-оценочных работ … Независимый промышленный эксперт Максим Худалов оценивает затраты на '
  'геологическое изучение в 100–250 млн руб. На Камчатке, по его словам, ценник может увеличиться в два раза из-за '
  'нехватки техники и персонала.',
  'https://www.kommersant.ru/doc/7796300'),
 ('gd88cbe9a',
  'eco.val',
  'Объем финансирования проектов «Гейзер Голд» оценивается в 96 млн и 95 млн рублей.',
  'Цену стороны не раскрыли. По словам старшего менеджера «S+ Консалтинг» Дмитрия Гомера, в цене, вероятно, учтен '
  'дисконт за сложную логистику, высокую сейсмичность и отсутствие инфраструктуры.',
  'Старший менеджер «S+ Консалтинг» Дмитрий Гомер говорит, что участки находятся на ранней стадии поисково-оценочных '
  'работ … сделка может быть своевременной, тем более что дисконт, вероятно, учитывал экстремальную логистику, '
  'высокую сейсмичность и отсутствие инфраструктуры.',
  'https://www.kommersant.ru/doc/7796300'),
 ('gd88cbe9a',
  'law.struct',
  '«Гейзер Голд» с лета 2022 держит лицензии на геологоизучение участков Нимаевский и Кларин в Усть-Камчатском '
  'районе. По данным Роснедр, с III кв. 2023 компания собиралась искать и оценивать на них рудное золото и серебро. '
  'Геологоизучение должно завершиться во II кв. 2029.',
  '3 июня 2025 года 100% долей ООО «Гейзер Голд» перешли от ООО «Гиперспэйс» к МКАО «Ареал» — структуре «Хайлэнд '
  'Голд».',
  '3 июня 2025 года — ООО "ГИПЕРСПЭЙС" вышел из состава участников доля 100.0%. 3 июня 2025 года — МКАО "АРЕАЛ" '
  'вошел в состав участников доля 100.0%. … Структура «Хайлэнд Голд» Владислава Свиблова 3 июня стала владельцем '
  'компании «Гейзер Голд» с лицензиями на геологическое изучение месторождений золота и серебра на Камчатке, следует '
  'из данных ЕГРЮЛ и Роснедр. Прежним собственником «Гейзер Голд» было ООО «Гиперспэйс», основанное бывшим '
  'совладельцем Челябинского трубопрокатного завода (ЧТПЗ) Андреем Комаровым',
  'https://projectcompass.ru/api/companies/g849d19d0/fns'),
 ('gd88cbe9a',
  'eco.context',
  'Прежним собственником «Гейзер Голд» было ООО «Гиперспэйс», которое на 80,9% принадлежит АО «Старт» (19% — Андрею '
  'Комарову). «Гиперспэйсу» также принадлежат ООО «Варна Минералз» и ООО «Гора: Голден Ратио», в которое входят ООО '
  '«Желтугинская ГРК», ООО «Камчатская горная компания» и «Тихоокеанская горная компания». «Старту» принадлежит 100% '
  'долей ООО «Федорово Минералз».',
  '«Гейзер Голд» зарегистрирована в Москве в феврале 2021 года. С лета 2022 года компания владеет двумя лицензиями '
  'на геологоразведку — участки Нимаевский и Кларин в Усть-Камчатском районе; они относятся к золотоносному '
  'Охотско-Чукотскому поясу. По данным Роснедр, работы по поиску и оценке рудного золота и серебра компания '
  'собиралась вести с третьего квартала 2023 года до второго квартала 2029 года, на два проекта заложено 96 млн и 95 '
  'млн ₽.\n'
  '\n'
  'ООО «Гиперспэйс» основал бывший совладелец Челябинского трубопрокатного завода Андрей Комаров. По одним данным, '
  '80,9% «Гиперспэйса» принадлежит АО «Старт», 19% — Комарову; по другим, владелец 99,9% компании в ЕГРЮЛ скрыт. '
  'Начальник аналитического отдела «Риком-Траста» Олег Абелев допускает, что прежний владелец вышел из актива, чтобы '
  'перенаправить инвестиции, из-за нехватки экспертизы или опасений, что разведка обойдется дороже плана.',
  'C лета 2022 года «Гейзер Голд» владеет лицензиями на геологическое изучение участков Нимаевский и Кларин в '
  'Усть-Камчатском районе. Согласно данным Роснедр, с третьего квартала 2023 года предприятие планировало вести на '
  'них поисково-оценочные работы на рудное золото и серебро, срок окончания ГИН намечен на второй квартал 2029 года. '
  'Объем финансирования проектов «Гейзер Голд» оценил в 96 млн и 95 млн рублей соответственно. «Гезер Голд» '
  'зарегистрировано в Москве в феврале 2021 года, прежний собственник – ООО «Гиперспейс», которое на 80,9% '
  'принадлежит АО «Старт» (19% владеет Андрей Комаров). … среди преимуществ — принадлежность к золотоносному '
  'Охотско-Чукотскому поясу … Структура «Хайлэнд Голд» Владислава Свиблова 3 июня стала владельцем компании «Гейзер '
  'Голд» с лицензиями на геологическое изучение месторождений золота и серебра на Камчатке, следует из данных ЕГРЮЛ '
  'и Роснедр. Прежним собственником «Гейзер Голд» было ООО «Гиперспэйс», основанное бывшим совладельцем Челябинского '
  'трубопрокатного завода (ЧТПЗ) Андреем Комаровым … Сейчас собственник 99,9% «Гиперспэйс» в ЕГРЮЛ скрыт, 0,1% '
  'принадлежит самой компании. В Highland Gold отказались от комментариев. … Начальник аналитического отдела '
  'инвестиционной компании «Риком-Траст» Олег Абелев считает, что прежний владелец мог выйти из актива из-за '
  'необходимости переориентировать инвестиции, нехватки экспертизы либо опасений, что расходы на разведку превышают '
  'запланированные.',
  'https://zolteh.ru/junior/khaylend-gold-priobrela-poiskovye-aktivy-na-kamchatke/'),
 ('g15f35a5d',
  'sum',
  'Не разглашается (возможная сумма сделки — $400 млн, согласно открытым источникам)',
  '$400 млн (по оценке)',
  'лашается (возможная сумма сделки — $400 млн, согласно открытым источникам)',
  'https://www.kommersant.ru/doc/8077927'),
 ('g15f35a5d',
  'eco.sum',
  'Не разглашается (возможная сумма сделки — $400 млн, согласно открытым источникам)',
  '$400 млн (по оценке)',
  'лашается (возможная сумма сделки — $400 млн, согласно открытым источникам)',
  'https://www.kommersant.ru/doc/8077927'),
 ('g15f35a5d',
  'eco.share',
  '—',
  '100% акций МКАО «Западная Голд Майнинг Лимитед»',
  '100% акций МКАО «Западная Голд Майнинг Лимитед» приобрела группа «ОКТО»',
  'https://zolteh.ru/news/gruppa_okto_priobrela_100_aktsiy_zolotodobyvayushchey_gk_zapadnaya/'),
 ('g15f35a5d',
  'eco.val',
  '—',
  'Сумму стороны не раскрыли. В обзоре сделок года по данным юридической фирмы BIRCH, консультанта продавцов, '
  'возможная сумма сделки названа $400 млн со ссылкой на открытые источники.',
  'лашается (возможная сумма сделки — $400 млн, согласно открытым источникам) … Юридическая фирма, сопровождающая '
  'сделку: BIRCH со стороны продавца',
  'https://www.kommersant.ru/doc/8077927'),
 ('g15f35a5d',
  'eco.fin',
  'В 2023 году компания добыла 3,4 тонны золота, чистая прибыль составила около 1,86 млрд ₽, выручка — 5,83 млрд ₽. '
  'АО ГРК «Западная» в 2025 году увеличило чистую прибыль по РСБУ в 7,79 раза, до 7,869 млрд ₽, — в основном за счет '
  '10,935 млрд ₽ дивидендов от дочернего ООО «АС Западная» (рудник «Кедровский» в Бурятии); выручка от продаж '
  'выросла на 28,8%, до 7,146 млрд ₽. Сам ГОК «Кедровский» (бывшая А/С «Западная») в 2025 году увеличил выручку на '
  '18,2%, до 13,477 млрд ₽, прибыль от продаж — на 84,8%, до 7,032 млрд ₽, чистую прибыль — на 34,9%, до 3,709 млрд '
  '₽.',
  '—',
  'В 2023 году компания добыла 3,4 тонны золота, чистая прибыль составила около 1,86 млрд рублей, выручка – 5,83 '
  'млрд рублей.',
  'https://abireg.ru/newsitem/106857/'),
 ('g15f35a5d',
  'eco.target_fin',
  'Производство золота у ГК «Западная» в 2023 году — 108 871 унция. Из 13 проектов группы 10 пока на разведке; '
  'золото добывают на двух подземных рудниках, Бадране и Кедровке, и открытым способом на ГОКе Александровское. '
  'Проекты расположены в Якутии, Бурятии и Забайкалье, а сама группа существует 40 лет.',
  'Группа «Западная» добыла в 2023 году 3,4 т золота (108,87 тыс. унций) при выручке 5,83 млрд ₽ и чистой прибыли '
  'около 1,86 млрд ₽. У нее более 90 т утвержденных запасов и 390 т ресурсов.',
  'В 2023 году «Западная» произвела 108,87 тыс. унций золота (+2% к 2022 году). … В 2023 году компания добыла 3,4 '
  'тонны золота, чистая прибыль составила около 1,86 млрд рублей, выручка – 5,83 млрд рублей. … Утвержденные запасы '
  'золота компании превышают 90 т, а ресурсы — 390 т.',
  'https://www.rbc.ru/business/25/04/2025/680b35279a79473cf11967ae'),
 ('g15f35a5d',
  'law.struct',
  'Приобретение до 100% голосующих акций МКАО «Западная Голд Майнинг Лимитед». Все стратегические решения будут '
  'приниматься в Москве, в офисе «ОКТО-Золото»: управление горнорудными компаниями предполагает взаимодействие с '
  'федеральными органами власти, в первую очередь надзорными.',
  'АО «ОКТО Золото» купило у менеджмента и миноритариев 100% голосующих акций МКАО «Западная Голд Майнинг Лимитед», '
  'головной компании группы. Сделку закрыли 25 апреля 2025 года.',
  'Как следует из базы решений Федеральной антимонопольной службы, в начале апреля АО «ОКТО Золото» получило '
  'предварительное согласие регулятора на приобретение до 100% голосующих акций МКАО «Западная Голд Майнинг '
  'Лимитед». Источник РБК сообщил, что сделка была закрыта в пятницу, 25 апреля … Сделка предусматривала '
  'установление инвестором контроля над активом посредством приобретения акций холдинговой компании группы у '
  'менеджмента и миноритариев. … 25 апреля 2025, 13:01',
  'https://www.rbc.ru/business/25/04/2025/680b35279a79473cf11967ae'),
 ('g15f35a5d',
  'law.appr',
  'Сделка потребовала согласия ФАС России; его получение сопровождала команда LEVEL Legal Services, которая также '
  'провела всестороннюю юридическую проверку приобретаемой группы компаний и консультировала покупателя по другим '
  'вопросам сделки.',
  'Предварительное согласие ФАС на покупку до 100% голосующих акций МКАО «Западная Голд Майнинг Лимитед» АО «ОКТО '
  'Золото» получило в начале апреля 2025 года.',
  'Как следует из базы решений Федеральной антимонопольной службы, в начале апреля АО «ОКТО Золото» получило '
  'предварительное согласие регулятора на приобретение до 100% голосующих акций МКАО «Западная Голд Майнинг '
  'Лимитед». Источник РБК сообщил, что сделка была закрыта в пятницу, 25 апреля … 25 апреля 2025, 13:01',
  'https://www.rbc.ru/business/25/04/2025/680b35279a79473cf11967ae'),
 ('g15f35a5d',
  'eco.context',
  'В 2024 году предприятия холдинга произвели в совокупности менее 3 т золота; некоторое снижение по сравнению с '
  'предыдущим годом руководство компании связывает со сложностями в приобретении и доставке запчастей и с дефицитом '
  'кадров. На 2025 год предприятия ГК «Западная» планировали произвести 3,207 т золота. Группа «ОКТО Золото» сменила '
  'название ООО «А/С Западная» на ГОК «Кедровский» и намерена создать предприятие с добычей более шести тонн золота '
  'в год.',
  'У «Западной» 40-летняя история и 13 проектов в Якутии, Бурятии и Забайкалье; золото добывают подземные рудники '
  'Бадран и Кедровка и карьер горно-обогатительного комплекса Александровское. До сделки, по данным группы, 65,41% '
  'акций держал менеджмент, 25,06% составлял казначейский пакет, 9,53% были у миноритариев.\n'
  '\n'
  'ОКТО — частная группа, которая добывает уголь и золото: с 2021 года в нее входит «Разрез Степной» в Хакасии, в '
  '2024 году она вместе с партнерами купила у «Полюса» ЗДК «Лензолото». Бенефициары группы не раскрываются. В июле '
  '2026 года «ОКТО Золото» переименовала ООО «А/С Западная» в ГОК «Кедровский».',
  'ГК «Западная» – группа российских золотодобывающих компаний с 40-летней историей. «Западная» ведет 13 проектов, '
  'расположенных в Бурятии, Якутии и Забайкальском крае: 2 подземных рудника, Бадран и Кедровка, '
  'горно-обогатительный комплекс по добыче руды открытым способом Александровское и 10 проектов на этапе разведки. … '
  'По данным самой группы, контроль принадлежал ее менеджменту (65,41% акций), 25,06% — казначейский пакет, 9,53% — '
  'миноритарии. … С 2021 года в нее входит угольный «Разрез Степной» в Хакасии. Конкретные бенефициары группы не '
  'раскрываются. … Покупателем стала группа «Окто», которая в 2024 году совместно с партнерами приобрела у компании '
  '«Полюс» ЗДК «Лензолото». … Группа «ОКТО Золото» переименовала ООО «А/С Западная» в ГОК «Кедровский» … 23 июля '
  '2026',
  'https://www.rbc.ru/business/25/04/2025/680b35279a79473cf11967ae'),
 ('g15f35a5d',
  'eco.rationale',
  None,
  'По неофициальным данным, с новым владельцем «Западная» будет активнее покупать участки и производственные активы, '
  'чтобы расширить сырьевую базу и нарастить добычу. Шеф-редактор журнала «Золото и технологии» Михаил Лесков '
  'считает, что «ОКТО» диверсифицирует активы и собирает портфель золотодобывающих проектов.',
  '«С новым владельцем ГК «Западная» намерена активизировать покупку новых участков и производственных активов для '
  'расширения сырьевой базы и увеличения объемов добычи», - рассказал собеседник. … «Цели группы «ОКТО» '
  'представляются достаточно очевидными: диверсифицировать свои активы и сформировать портфель производственных '
  'проектов в одном из наиболее динамично развивающихся секторов российской промышленности — золотодобыче», - '
  'комментирует сделку шеф-редактор журнала «Золото и технологии» Михаил Лесков.',
  'https://zolteh.ru/news/gruppa_okto_priobrela_100_aktsiy_zolotodobyvayushchey_gk_zapadnaya/'),
 ('g15f35a5d',
  'extra',
  'Сделка — покупка 100% акционерного капитала МКАО «Западная Голд Майнинг Лимитед» группой ОКТО. Собственники до '
  'сделки: менеджмент 65,41%, казначейский пакет 25,06%, миноритарии 9,53%. ОКТО — частная многопрофильная группа по '
  'добыче полезных ископаемых (уголь, золото); в 2024 году она приобрела у Полюса ЗДК «Лензолото» и владеет угольным '
  '«Разрезом Степной» в Хакасии.',
  'Группа ОКТО, которая в 2024 году купила у «Полюса» «Лензолото», получила еще одного золотодобытчика: «Западная» '
  'производит около 3 т золота в год и входит в топ-15 крупнейших в России.',
  'Покупателем стала группа «Окто», которая в 2024 году совместно с партнерами приобрела у компании «Полюс» ЗДК '
  '«Лензолото». … ГРК «Западная» входит в топ-15 крупнейших золотодобытчиков России с годовым производством около 3 '
  'тонн золота.',
  'https://abireg.ru/newsitem/106857/'),
 ('gbc0b68bd',
  'asset',
  None,
  'ООО «Фэшн фэктори»',
  'Производитель косметики и парфюмерии «Фаберлик» продал 100% долей в ООО «Фэшн фэктори» (управляет фабрикой по '
  'пошиву одежды в Ивановской области) структуре «Военторга» – ООО «Воентекстильпром». Изменения в ЕГРЮЛе '
  'зарегистрированы 10 апреля',
  'https://www.vedomosti.ru/business/articles/2025/04/21/1105538-faberlik-prodala-fabriku-po-poshivu-odezhdi'),
 ('gbc0b68bd',
  'title',
  '«Фаберлик» продала фабрику по пошиву одежды «Воентекстильпрому»',
  '«Воентекстильпром» купил «Фэшн фэктори» у «Фаберлика»',
  'Производитель косметики и парфюмерии «Фаберлик» продал 100% долей в ООО «Фэшн фэктори» (управляет фабрикой по '
  'пошиву одежды в Ивановской области) структуре «Военторга» – ООО «Воентекстильпром». Изменения в ЕГРЮЛе '
  'зарегистрированы 10 апреля',
  'https://www.vedomosti.ru/business/articles/2025/04/21/1105538-faberlik-prodala-fabriku-po-poshivu-odezhdi'),
 ('gbc0b68bd',
  'sum',
  '150 млн ₽ (по оценке)',
  'До 150 млн ₽ (по оценке)',
  'Гендиректор «INFOLine-аналитики» Михаил Бурмистров оценил стоимость актива в сумму не более 150 млн руб.',
  'https://www.retail.ru/news/kompaniya-faberlik-prodala-fabriku-po-poshivu-odezhdy-strukture-voentorga-21-aprelya-2025-263762/'),
 ('gbc0b68bd',
  'eco.sum',
  '150 млн ₽ (по оценке)',
  'До 150 млн ₽ (по оценке)',
  'Гендиректор «INFOLine-аналитики» Михаил Бурмистров оценил стоимость актива в сумму не более 150 млн руб.',
  'https://www.retail.ru/news/kompaniya-faberlik-prodala-fabriku-po-poshivu-odezhdy-strukture-voentorga-21-aprelya-2025-263762/'),
 ('gbc0b68bd',
  'eco.share',
  '—',
  '100% долей ООО «Фэшн фэктори»',
  'Производитель косметики и парфюмерии «Фаберлик» продал 100% долей в ООО «Фэшн фэктори» (управляет фабрикой по '
  'пошиву одежды в Ивановской области) структуре «Военторга» – ООО «Воентекстильпром». Изменения в ЕГРЮЛе '
  'зарегистрированы 10 апреля',
  'https://www.vedomosti.ru/business/articles/2025/04/21/1105538-faberlik-prodala-fabriku-po-poshivu-odezhdi'),
 ('gbc0b68bd',
  'law.adv',
  [['Стороны сделки', 'Не раскрывались', 'Юридические консультанты в публичных источниках не раскрывались']],
  [],
  'Производитель косметики и парфюмерии «Фаберлик» продал 100% долей в ООО «Фэшн фэктори» (управляет фабрикой по '
  'пошиву одежды в Ивановской области) структуре «Военторга» – ООО «Воентекстильпром». Изменения в ЕГРЮЛе '
  'зарегистрированы 10 апреля',
  'https://www.vedomosti.ru/business/articles/2025/04/21/1105538-faberlik-prodala-fabriku-po-poshivu-odezhdi'),
 ('gbc0b68bd',
  'eco.context',
  '«Воентекстильпром» шьет форму для Минобороны РФ и МЧС, у него шесть фабрик на Северном Кавказе. Аслану Аталикову '
  'в компании принадлежит 64%, АО «Военторг» — 26%, Залиму Кардангушеву — 10%. Сам «Фаберлик» приобрел и обновил '
  'завод в Чехове (Московская обл.), где планируют выпускать бытовую химию.',
  '«Воентекстильпром» шьет форму для Минобороны и МЧС, у него шесть фабрик в Карачаево-Черкесии и '
  'Кабардино-Балкарии. 64% компании принадлежат Аслану Аталикову, 26% — АО «Военторг», 10% — Залиму Кардангушеву.\n'
  '\n'
  '«Фаберлик» продает одежду с 2013 года, фабрику в Ивановской области запустил в 2017 году; она может выпускать до '
  '750 тыс. изделий в год — футболки, водолазки, мужское белье и другой трикотаж. «Фаберлик» купил и модернизировал '
  'завод в Чехове (Московская область), где планирует выпускать бытовую химию.',
  'Структура «Военторга» ООО «Воентекстильпром» специализируется на пошиве вещей и обмундирования для нужд '
  'Минобороны и МЧС. В настоящее время у нее шесть фабрик в Карачаево-Черкесии и Кабардино-Балкарии. … Основными '
  'владельцами «Воентекстильпрома» являются Аслан Аталиков (64%), АО «Военторг» (26%) и Залим Кардангушев (10%). … '
  '«Фаберлик» занимается продажами одежды с 2013 года, а в 2017 году компания запустила собственную фабрику. На ней '
  'производились трикотажные изделия — футболки, водолазки, мужское нижнее белье, а также изделия из футера. … '
  'Мощности фабрики позволяют выпускать до 750 тыс. единиц продукции ежегодно … В частности, «Фаберлик» приобрел и '
  'модернизировал завод в Чехове Московской области, на котором планируется организовать производство бытовой химии.',
  'https://www.retail.ru/news/kompaniya-faberlik-prodala-fabriku-po-poshivu-odezhdy-strukture-voentorga-21-aprelya-2025-263762/'),
 ('gbc0b68bd',
  'extra',
  'Фабрику продал «Фаберлик», производитель парфюмерно-косметической продукции. Купило ее ООО «Воентекстильпром», '
  'которое шьет военное обмундирование для Минобороны и МЧС. Предмет сделки — ООО «Фэшн фэктри» с фабрикой в '
  'Ивановской области мощностью 750 тыс. изделий в год.',
  '«Фаберлик» продал швейную фабрику в Ивановской области производителю военной формы «Воентекстильпром», связанному '
  'с «Военторгом».',
  'Производитель косметики и парфюмерии «Фаберлик» продал 100% долей в ООО «Фэшн фэктори» (управляет фабрикой по '
  'пошиву одежды в Ивановской области) структуре «Военторга» – ООО «Воентекстильпром». Изменения в ЕГРЮЛе '
  'зарегистрированы 10 апреля … Структура «Военторга» ООО «Воентекстильпром» специализируется на пошиве вещей и '
  'обмундирования для нужд Минобороны и МЧС. В настоящее время у нее шесть фабрик в Карачаево-Черкесии и '
  'Кабардино-Балкарии.',
  'https://www.vedomosti.ru/business/articles/2025/04/21/1105538-faberlik-prodala-fabriku-po-poshivu-odezhdi'),
 ('g181d7687',
  'title',
  '«КНС Групп» (Yadro) приобрела 38% доли в «КБ БОРЕЙ»',
  'Yadro купил 38% «КБ Борей»',
  'Входящая в «ИКС Холдинг» «КНС Групп» (работает под брендом Yadro) 31 января стала владельцем 38% в компании — '
  'разработчике и производителе систем кондиционирования для центров обработки данных «КБ Борей» (бренд BOREY), '
  'следует из данных СПАРК.',
  'https://www.rbc.ru/technology_and_media/04/02/2025/67a1ecc09a7947034c102e35'),
 ('g181d7687',
  'sum',
  '100 млн ₽',
  '100 млн ₽ (по оценке)',
  'Аналитик ФГ "Финам" Леонид Делицын оценил сделку и предположил, во сколько могут обойтись в дальнейшем оставшиеся '
  '62% долей "КБ Борей": Состоявшуюся сделку можно оценить в 100 млн руб. Поскольку индустрия дата-центров будет '
  'расти высокими темпами, цена оставшейся доли может быть гораздо выше - несколько сотен миллионов рублей".',
  'https://www.comnews.ru/content/237587/2025-02-05/2025-w06/1007/yadro-priobrela-38-doley-kb-borey'),
 ('g181d7687',
  'eco.sum',
  '100 млн ₽',
  '100 млн ₽ (по оценке)',
  'Аналитик ФГ "Финам" Леонид Делицын оценил сделку и предположил, во сколько могут обойтись в дальнейшем оставшиеся '
  '62% долей "КБ Борей": Состоявшуюся сделку можно оценить в 100 млн руб. Поскольку индустрия дата-центров будет '
  'расти высокими темпами, цена оставшейся доли может быть гораздо выше - несколько сотен миллионов рублей".',
  'https://www.comnews.ru/content/237587/2025-02-05/2025-w06/1007/yadro-priobrela-38-doley-kb-borey'),
 ('g181d7687',
  'eco.share',
  'Доля Yadro — 1,9 млн ₽ из 5 млн ₽ уставного капитала «КБ Борей»; капитал не менялся с основания.',
  '38% долей ООО «КБ Борей»',
  'ООО "КНС Групп" (производитель IT-оборудования, бренд Yadro, входит в "ИКС Холдинг") приобрело 38% ООО "КБ Борей" '
  '(производитель систем охлаждения для ЦОД) в рамках запуска нового бизнес-направления по созданию продуктов для '
  'инженерной инфраструктуры дата-центров. По данным ЕГРЮЛ, сделка зарегистрирована 31 января.',
  'https://www.interfax.ru/business/1006209'),
 ('g181d7687',
  'law.adv',
  [['Стороны сделки', 'Не раскрывались', 'Юридические консультанты в публичных источниках не раскрывались']],
  [],
  'Входящая в «ИКС Холдинг» «КНС Групп» (работает под брендом Yadro) 31 января стала владельцем 38% в компании — '
  'разработчике и производителе систем кондиционирования для центров обработки данных «КБ Борей» (бренд BOREY), '
  'следует из данных СПАРК.',
  'https://www.rbc.ru/technology_and_media/04/02/2025/67a1ecc09a7947034c102e35'),
 ('g181d7687',
  'eco.val',
  'По оценке аналитика ФГ «Финам» Леонида Делицына, состоявшуюся сделку можно оценить в 100 млн ₽, а оставшиеся 62% '
  'долей «КБ Борей» могут обойтись гораздо дороже — в несколько сотен миллионов рублей, поскольку индустрия '
  'дата-центров будет расти высокими темпами.',
  'Стороны сумму не называли. Аналитик ФГ «Финам» Леонид Делицын оценивает сделку в 100 млн ₽, а оставшиеся 62% — в '
  'несколько сотен миллионов рублей, потому что рынок дата-центров будет быстро расти. Алексей Замесов из «Руцентра» '
  'считает, что 38% стоят не дороже 100 млн ₽, и не исключает продажу по номиналу при условии, что «КНС Групп» '
  'проинвестирует развитие компании.',
  'Аналитик ФГ "Финам" Леонид Делицын оценил сделку и предположил, во сколько могут обойтись в дальнейшем оставшиеся '
  '62% долей "КБ Борей": Состоявшуюся сделку можно оценить в 100 млн руб. Поскольку индустрия дата-центров будет '
  'расти высокими темпами, цена оставшейся доли может быть гораздо выше - несколько сотен миллионов рублей". … '
  'Руководитель спецпроектов «Руцентр» Алексей Замесов оценивает долю «КНС Групп» в 38% не более чем в 100 млн руб. '
  'Также возможно, что сделка могла быть совершена по номинальной стоимости с условием инвестиций «КНС Групп» в '
  'развитие компании, считает Замесов.',
  'https://www.comnews.ru/content/237587/2025-02-05/2025-w06/1007/yadro-priobrela-38-doley-kb-borey'),
 ('g181d7687',
  'eco.rationale',
  'Yadro открывает новое направление — продукты для инженерной инфраструктуры дата-центров — и хочет усилить позиции '
  'в этом сегменте; для этого ООО «КНС Групп» (бренд Yadro) купило 38% «КБ Борей», российского разработчика и '
  'производителя кондиционирования для ЦОД. Вести направление в Yadro будет Ратмир Трошин; по ЕГРЮЛ, остальные доли '
  'у соучредителей — 47% у Трошина, 15% сохранил Анатолий Ференцев. Директор по продуктам Yadro Павел Егоров '
  'объясняет сделку тем, что серверам, в том числе для ИИ, нужно много энергии и все более совершенное охлаждение — '
  'от чипов до стоек и ЦОДов. Вместе с экспертизой «КБ Борей» опыт Yadro, по его мнению, позволит предложить '
  'клиентам отечественные решения для управления данными — комплексные и более эффективные.',
  'Yadro запускает направление продуктов для инженерной инфраструктуры дата-центров. Директор по продуктам Yadro '
  'Павел Егоров объясняет покупку тем, что серверам, в том числе для задач ИИ, нужно много энергии и все более '
  'совершенное охлаждение — от чипов до стоек и ЦОДов, а вместе с опытом «КБ Борей» компания сможет предложить '
  'клиентам комплексные российские решения.',
  'ООО "КНС Групп" (производитель IT-оборудования, бренд Yadro, входит в "ИКС Холдинг") приобрело 38% ООО "КБ Борей" '
  '(производитель систем охлаждения для ЦОД) в рамках запуска нового бизнес-направления по созданию продуктов для '
  'инженерной инфраструктуры дата-центров. По данным ЕГРЮЛ, сделка зарегистрирована 31 января. … "Современное '
  'серверное оборудование, в том числе, применяемое для задач ИИ, требует значительных энергоресурсов и, как '
  'следствие - постоянного совершенствования систем охлаждения на всех уровнях - от охлаждения чипов до решений на '
  'уровне стоек и ЦОДов. Объединив собственный опыт с экспертизой "КБ Борей", мы сможем предложить нашим клиентам '
  'ещё более эффективные комплексные отечественные решения для управления данными", - отметил директор по продуктам '
  'Yadro Павел Егоров',
  'https://www.interfax.ru/business/1006209'),
 ('g181d7687',
  'eco.context',
  'Основанная в 2016 году компания «КБ Борей» занимается проектированием, производством, продажей и обслуживанием '
  'климатического оборудования. В частности, компания запатентовала технологию воздухораспределения в '
  'телекоммуникационных шкафах, разработала технологию использования воздушного рекуператора для фрикулинга в '
  'мини-ЦОД уличного исполнения. В июле 2026 года Yadro представила комплексное решение гибридной системы охлаждения '
  'ЦОД, объединяющее преимущества воздушного и жидкостного типов охлаждения. Оно состоит из инженерного контура '
  'BOREY «Посейдон», включающего драйкулер с гидравликой и блок распределения охлаждающей жидкости, а также '
  'вычислительных комплексов RACKSCALE с водоподготовкой. Ключевые особенности решения — технология Direct Liquid '
  'Cooling, позволяющая точечно отводить тепло от CPU и GPU, и блок распределения охлаждения БРО-300, равномерно '
  'подающий охлаждающую жидкость между серверными стойками.',
  '«КБ Борей», зарегистрированная в 2017 году, проектирует, производит, продает и обслуживает системы охлаждения для '
  'центров обработки данных. Среди ее разработок — способ распределять воздух в телекоммуникационных шкафах и '
  'фрикулинг через воздушный рекуператор для уличных мини-ЦОДов. Остальные доли сохранили соучредители: 47% у '
  'директора по развитию Ратмира Трошина, который будет вести новое направление в Yadro, 15% у Анатолия Ференцева.\n'
  '\n'
  'В июле 2026 года Yadro представила гибридную систему охлаждения ЦОД, в которую входит инженерный контур BOREY '
  '«Посейдон».',
  'ООО "КБ Борей" зарегистрировано в 2017 году, уставный капитал - 5 млн рублей. … Компания владеет собственной '
  'технологией воздухораспределения в телекоммуникационных шкафах, технологией использования воздушного рекуператора '
  'для фрикулинга (энергосберегающее решение для охлаждения) в мини-ЦОДе уличного исполнения … По данным ЕГРЮЛ, '
  'оставшиеся доли "КБ Борей" сохранили соучредители компании - Ратмир Трошин (47%), который также будет отвечать за '
  'развитие нового направления в компании Yadro, и Анатолий Ференцев (15%). … BOREY «Посейдон» … 2026',
  'https://www.rbc.ru/technology_and_media/04/02/2025/67a1ecc09a7947034c102e35'),
 ('g181d7687',
  'eco.target_fin',
  'Выручка ООО «КБ Борей» в 2023 году составила 43,1 млн ₽ — втрое больше, чем в 2022 году (14,1 млн ₽). Чистая '
  'прибыль при этом снизилась на 83,2%: 107 тыс. ₽ против 638 тыс. ₽ годом ранее. За 2024 год прибыль составила 323 '
  '000 ₽, выручка — 85 342 000 ₽.',
  'Выручка ООО «КБ Борей» за 2023 год — 43,1 млн ₽, втрое больше, чем в 2022 году (14,1 млн ₽); чистая прибыль '
  'снизилась на 83,2%, до 107 тыс. ₽. За 2024 год выручка — 85,3 млн ₽, чистая прибыль — 117 тыс. ₽.',
  'По данным bo.nalog.ru выручка ООО "КБ Борей" в 2023 г. составила 43,1 млн руб., что в три раза больше, чем в 2022 '
  'г., - 14,1 млн руб. Однако чистая прибыль компании в 2023 г. снизилась на 83,2% по сравнению с тем же показателем '
  'за 2022 г. - 107 тыс. руб. против 638 тыс. руб. … Отчетность за 2024 год (РСБУ): выручка 85342000 ₽, чистая '
  'прибыль 117000 ₽.',
  'https://www.comnews.ru/content/237587/2025-02-05/2025-w06/1007/yadro-priobrela-38-doley-kb-borey'),
 ('g181d7687',
  'law.struct',
  '—',
  'Продавец, Александр Калинин, по его словам, владел долей через третьих лиц, это была семейная доля. Переход 38% к '
  'ООО «КНС Групп» записан в ЕГРЮЛ 31 января 2025 года.',
  'Продавцом пакета выступил российский IT-предприниматель и инвестор, основатель Национальной компьютерной '
  'корпорации Александр Калинин. Он пояснил РБК, что эта доля принадлежала ему через третьих лиц. «Мы действительно '
  'продали семейную долю в этом активе … ООО "КНС Групп" (производитель IT-оборудования, бренд Yadro, входит в "ИКС '
  'Холдинг") приобрело 38% ООО "КБ Борей" (производитель систем охлаждения для ЦОД) в рамках запуска нового '
  'бизнес-направления по созданию продуктов для инженерной инфраструктуры дата-центров. По данным ЕГРЮЛ, сделка '
  'зарегистрирована 31 января. … 14:04, 4 февраля 2025',
  'https://www.rbc.ru/technology_and_media/04/02/2025/67a1ecc09a7947034c102e35'),
 ('g94683ed2',
  'eco.rationale',
  'По словам пресс-службы, присоединение «Рив Гош», одной из крупнейших сетей, к Wildberries позволит развить '
  'омниканальные продажи, заметно расширить ассортимент брендов на виртуальной витрине и сделать товары категории '
  '«Красота» доступнее для покупателей в регионах и странах присутствия.',
  'Wildberries & Russ объясняет покупку развитием омниканальных продаж: с «Рив Гош» маркетплейс получает больше '
  'брендов и может доставлять косметику покупателям в регионах и других странах.',
  '"Присоединение к Wildberries одной из крупнейших сетей "Рив Гош" позволит развить омниканальные продажи, '
  'значительно расширить ассортимент брендов на виртуальной витрине и обеспечить доступность товаров категории '
  '"Красота" для покупателей в регионах и странах присутствия"',
  'https://www.interfax.ru/business/1063390')]

_SET = [('gfa14411d', 'date_basis', None, 'registry'),
 ('g55f1c662', 'date_basis', None, 'registry'),
 ('g57b3b93c', 'date_basis', None, 'announcement'),
 ('g1059432d', 'date_basis', None, 'closing'),
 ('gfc7e5649', 'date_basis', None, 'registry'),
 ('gc677124b', 'date_basis', None, 'registry'),
 ('g94683ed2', 'date_basis', None, 'registry'),
 ('ga0a49202', 'date_basis', None, 'closing'),
 ('gd88cbe9a', 'date_basis', None, 'registry'),
 ('g15f35a5d', 'date_basis', None, 'closing'),
 ('gbc0b68bd', 'date_basis', None, 'registry'),
 ('g94683ed2', 'sum_basis', None, 'estimate'),
 ('g15f35a5d', 'sum_basis', None, 'estimate'),
 ('gbc0b68bd', 'sum_basis', None, 'estimate'),
 ('g181d7687', 'ind', 'ИТ и интернет', 'Машиностроение'),
 ('gfa14411d',
  'src',
  [['KSE Institute — Leave Russia', 'https://leave-russia.org/lpp-group'],
   ['Интерфакс', 'https://www.interfax.ru'],
   ['Коммерсантъ', 'https://www.kommersant.ru/doc/5446520'],
   ['Коммерсантъ', 'https://www.kommersant.ru/doc/5652618'],
   ['Hindenburg Research', 'https://hindenburgresearch.com/lpp/'],
   ['Notes from Poland',
    'https://notesfrompoland.com/2025/07/11/polish-retail-giant-lpp-accepts-1-8m-zloty-fine-over-disclosure-failings-linked-to-russia-exit/'],
   ['Omnichannel News', 'https://omnichannelnews.pl/2026/04/22/bledy-ksiegowe-lpp-knf-naklada-15-mln-zl-kary/']],
  [['Коммерсантъ', 'https://www.kommersant.ru/doc/5446520'],
   ['Коммерсантъ', 'https://www.kommersant.ru/doc/5652618'],
   ['Пепеляев Групп',
    'https://www.pgplaw.com/upload/iblock/0c7/qtphlbgforz2fcytqxc2r7fathr0mtya/2025_Corporate_eng.pdf'],
   ['Hindenburg Research', 'https://hindenburgresearch.com/lpp/'],
   ['Notes from Poland',
    'https://notesfrompoland.com/2025/07/11/polish-retail-giant-lpp-accepts-1-8m-zloty-fine-over-disclosure-failings-linked-to-russia-exit/'],
   ['Omnichannel News', 'https://omnichannelnews.pl/2026/04/22/bledy-ksiegowe-lpp-knf-naklada-15-mln-zl-kary/'],
   ['KSE Institute — Leave Russia', 'https://leave-russia.org/lpp-group']]),
 ('g55f1c662',
  'src',
  [['KSE Institute — Leave Russia', 'https://leave-russia.org/valio'],
   ['Retail.ru',
    'https://www.retail.ru/news/rossiyskaya-dochka-valio-pereshla-v-sobstvennost-benefitsiara-velkoma-12-yanvarya-2023-224567/'],
   ['Castren & Snellman', 'https://castren.fi/cases/cases-2022/valio3'],
   ['Интерфакс', 'https://www.interfax.ru/business/1018641'],
   ['TAdviser', 'https://www.tadviser.ru/index.php/Компания:Viola_(Виола)']],
  [['Retail.ru',
    'https://www.retail.ru/news/rossiyskaya-dochka-valio-pereshla-v-sobstvennost-benefitsiara-velkoma-12-yanvarya-2023-224567/'],
   ['Castren & Snellman', 'https://castren.fi/cases/cases-2022/valio3'],
   ['ЕГРЮЛ', 'https://projectcompass.ru/api/companies/g54913880/fns'],
   ['Интерфакс', 'https://www.interfax.ru/business/1018641'],
   ['TAdviser', 'https://www.tadviser.ru/index.php/Компания:Viola_(Виола)'],
   ['KSE Institute — Leave Russia', 'https://leave-russia.org/valio']]),
 ('g57b3b93c',
  'src',
  [['KSE Institute — Leave Russia', 'https://leave-russia.org/mm-packaging'],
   ['Printindustry.ru', 'https://printindustry.ru/mm-packaging-prodala-svoi-rossiyskie-predpriyatiya/'],
   ['CMS Law',
    'https://cms.law/de/aut/news-information/mayr-melnhof-packaging-verkauft-russische-standorte-mit-rechtlicher-begleitung-von-cms'],
   ['Псковская Лента Новостей', 'https://pln-pskov.ru/society/542100.html'],
   ['Фонтанка', 'https://www.fontanka.ru/2025/01/11/74977775/']],
  [['Mayr-Melnhof Group', 'https://mm.group/news/press-releases/mm-packaging-divests-production-sites-in-russia/'],
   ['CMS Law',
    'https://cms.law/de/aut/news-information/mayr-melnhof-packaging-verkauft-russische-standorte-mit-rechtlicher-begleitung-von-cms'],
   ['Фонтанка', 'https://www.fontanka.ru/2025/01/11/74977775/'],
   ['AK&M', 'https://www.akm.ru/eng/news/sveza-acquired-three-paper-and-cardboard-manufacturing-companies/'],
   ['Псковская Лента Новостей', 'https://pln-pskov.ru/society/542100.html'],
   ['Printindustry.ru', 'https://printindustry.ru/mm-packaging-prodala-svoi-rossiyskie-predpriyatiya/'],
   ['KSE Institute — Leave Russia', 'https://leave-russia.org/mm-packaging']]),
 ('g1059432d',
  'src',
  [['KSE Institute — Leave Russia', 'https://leave-russia.org/whirlpool'],
   ['Bloomberg', 'https://www.bloomberg.com'],
   ['Abireg', 'https://abireg.ru/newsitem/95576/'],
   ['Retail.ru',
    'https://www.retail.ru/news/turetskaya-kompaniya-arcelik-stala-vladeltsem-rossiyskogo-biznesa-whirlpool-28-sentyabrya-2022-220964/'],
   ['TAdviser',
    'https://www.tadviser.ru/index.php/Компания:IHPA_-_IHP_Appliances_Sales_-_Ай_Эйч_Пи_Апплаенсес_Сейлс_-_Вирлпул_Рус_(Whirlpool_Rus)']],
  [['Whirlpool (отчет 10-Q за III квартал 2022 года)',
    'https://www.sec.gov/Archives/edgar/data/106640/000010664022000138/whr-20220930.htm'],
   ['Whirlpool (отчет 10-Q за III квартал 2023 года)',
    'https://www.sec.gov/Archives/edgar/data/106640/000010664023000131/whr-20230930.htm'],
   ['Retail.ru',
    'https://www.retail.ru/news/turetskaya-kompaniya-arcelik-stala-vladeltsem-rossiyskogo-biznesa-whirlpool-28-sentyabrya-2022-220964/'],
   ['New Retail',
    'https://new-retail.ru/novosti/retail/turetskaya_arcelik_priobrela_rossiyskiy_biznes_whirlpool9593/'],
   ['Better Chance', 'https://betterchance.ru/en/news/better-chance-advises-arcelik-a-/'],
   ['Daily Sabah (Reuters)',
    'https://www.dailysabah.com/business/economy/turkish-home-appliance-maker-arcelik-takes-full-control-of-beko-europe'],
   ['Abireg', 'https://abireg.ru/newsitem/95576/'],
   ['TAdviser',
    'https://www.tadviser.ru/index.php/Компания:IHPA_-_IHP_Appliances_Sales_-_Ай_Эйч_Пи_Апплаенсес_Сейлс_-_Вирлпул_Рус_(Whirlpool_Rus)'],
   ['KSE Institute — Leave Russia', 'https://leave-russia.org/whirlpool']]),
 ('gfc7e5649',
  'src',
  [['KSE Institute — Leave Russia', 'https://leave-russia.org/softwareone'],
   ['ComNews',
    'https://www.comnews.ru/content/220241/2022-05-17/2022-w20/awara-it-poglotila-aktivy-softwareone-rossii'],
   ['TAdviser',
    'https://www.tadviser.ru/index.php/Компания:Wone_IT_(Ван_Ай_Ти_Трейд,_ранее_SoftwareONE_Россия,_СофтвэрУАН_и_Awara_IT_Russia,_Авара_Ай_Ти_Солюшенс)']],
  [['ComNews',
    'https://www.comnews.ru/content/220241/2022-05-17/2022-w20/awara-it-poglotila-aktivy-softwareone-rossii'],
   ['ЕГРЮЛ', 'https://projectcompass.ru/api/companies/ge90270b7/fns'],
   ['KSE Institute — Leave Russia', 'https://leave-russia.org/softwareone'],
   ['TAdviser',
    'https://www.tadviser.ru/index.php/Компания:Wone_IT_(Ван_Ай_Ти_Трейд,_ранее_SoftwareONE_Россия,_СофтвэрУАН_и_Awara_IT_Russia,_Авара_Ай_Ти_Солюшенс)']]),
 ('gc677124b',
  'src',
  [['KSE Institute — Leave Russia', 'https://leave-russia.org/aggreko-uk'],
   ['Интерфакс', 'https://www.interfax.ru/russia/1027809'],
   ['БурСервис (пресс-релиз о закрытии)', 'https://www.burservis.ru/news/20-11-25'],
   ['Denuo Legal — страница партнера Дениса Гаврилова', 'https://denuo.legal/ru/people/denis-gavrilov/'],
   ['Kremlin.ru (текст распоряжения)', 'http://www.kremlin.ru/acts/bank/51958/print'],
   ['Аггреко Евразия (объявление о смене собственника)', 'https://aggreko-eurasia.ru/about/news/smena-sobstvennika/'],
   ['АКМ', 'https://www.akm.ru/news/burservis_poluchil_razreshenie_na_pokupku_aktiva_aggreko/'],
   ['Итек.ru', 'https://itek.ru/news/burservis-poluchil-razreshenie-na-pokupku-rossijskogo-biznesa-aggreko/'],
   ['Коммерсантъ', 'https://www.kommersant.ru/doc/8442557']],
  [['БурСервис (пресс-релиз о закрытии)', 'https://www.burservis.ru/news/20-11-25'],
   ['Интерфакс', 'https://www.interfax.ru/russia/1027809'],
   ['Kremlin.ru (текст распоряжения)', 'http://www.kremlin.ru/acts/bank/51958/print'],
   ['ЕГРЮЛ', 'https://projectcompass.ru/api/companies/g69b9ab00/fns'],
   ['International Rental News', 'https://www.internationalrentalnews.com/news/russia-/8062061.article'],
   ['International Rental News',
    'https://www.internationalrentalnews.com/news/aggreko-finds-buyer-for-russian-business/8055543.article'],
   ['KSE Institute — Leave Russia', 'https://leave-russia.org/aggreko-uk'],
   ['Denuo Legal — страница партнера Дениса Гаврилова', 'https://denuo.legal/ru/people/denis-gavrilov/'],
   ['Аггреко Евразия (объявление о смене собственника)', 'https://aggreko-eurasia.ru/about/news/smena-sobstvennika/'],
   ['АКМ', 'https://www.akm.ru/news/burservis_poluchil_razreshenie_na_pokupku_aktiva_aggreko/'],
   ['Итек.ru', 'https://itek.ru/news/burservis-poluchil-razreshenie-na-pokupku-rossijskogo-biznesa-aggreko/'],
   ['Коммерсантъ', 'https://www.kommersant.ru/doc/8442557']]),
 ('g94683ed2',
  'src',
  [['Интерфакс', 'https://www.interfax.ru/business/1063390'],
   ['Коммерсантъ', 'https://www.kommersant.ru/doc/8077406'],
   ['Коммерсантъ', 'https://www.kommersant.ru/doc/8292342'],
   ['Malls.ru',
    'https://www.malls.ru/rus/news/riv-gosh-ukhodit-k-wildberries-zachem-marketpleysu-250-magazinov-krasoty.shtml']],
  [['Интерфакс', 'https://www.interfax.ru/business/1063390'],
   ['Коммерсантъ', 'https://www.kommersant.ru/doc/8292342'],
   ['Коммерсантъ', 'https://www.kommersant.ru/doc/8077406'],
   ['ЕГРЮЛ', 'https://projectcompass.ru/api/companies/g842a7fd2/fns'],
   ['Дякин, Горцунян и Партнеры',
    'https://dgpartners.legal/mediaportal/news/dgp-advises-on-the-sale-of-rive-gauche-group-/'],
   ['Malls.ru',
    'https://www.malls.ru/rus/news/riv-gosh-ukhodit-k-wildberries-zachem-marketpleysu-250-magazinov-krasoty.shtml']]),
 ('ga0a49202',
  'src',
  [['РБК', 'https://www.rbc.ru/technology_and_media/15/08/2025/689db55a9a7947b058474799'],
   ['Коммерсантъ', 'https://www.kommersant.ru/doc/7971462'],
   ['Inc.', 'https://incrussia.ru/news/krupnejshaya-set-kvestov-klaustrofobiya-pereshla-k-konkurentam/'],
   ['БГ (Большой город)', 'https://bg.ru/bg/business/comm-news/28940-kvesty-sold'],
   ['Sostav.ru', 'https://www.sostav.ru/publication/cet-kvestov-klaustrofobiya-smenila-vladeltsev-77407.html'],
   ['РБК', 'https://www.rbc.ru/technology_and_media/27/08/2024/66cc760e9a794719ed48a5bd'],
   ['Sostav.ru', 'https://www.sostav.ru/publication/set-kvestov-klaustrofobiya-proda-t-biznes-69680.html']],
  [['РБК', 'https://www.rbc.ru/technology_and_media/15/08/2025/689db55a9a7947b058474799'],
   ['Коммерсантъ', 'https://www.kommersant.ru/doc/7971462'],
   ['РБК', 'https://www.rbc.ru/technology_and_media/27/08/2024/66cc760e9a794719ed48a5bd'],
   ['Inc.', 'https://incrussia.ru/news/krupnejshaya-set-kvestov-klaustrofobiya-pereshla-k-konkurentam/'],
   ['БГ (Большой город)', 'https://bg.ru/bg/business/comm-news/28940-kvesty-sold'],
   ['Sostav.ru', 'https://www.sostav.ru/publication/cet-kvestov-klaustrofobiya-smenila-vladeltsev-77407.html'],
   ['Sostav.ru', 'https://www.sostav.ru/publication/set-kvestov-klaustrofobiya-proda-t-biznes-69680.html']]),
 ('gd88cbe9a',
  'src',
  [['Коммерсантъ', 'https://www.kommersant.ru/doc/7796300'],
   ['Золото и технологии', 'https://zolteh.ru/junior/khaylend-gold-priobrela-poiskovye-aktivy-na-kamchatke/'],
   ['EastRussia', 'https://www.eastrussia.ru/news/kompaniya-khaylend-gold-priobrela-aktivy-na-kamchatke/']],
  [['Коммерсантъ', 'https://www.kommersant.ru/doc/7796300'],
   ['ЕГРЮЛ', 'https://projectcompass.ru/api/companies/g849d19d0/fns'],
   ['Золото и технологии', 'https://zolteh.ru/junior/khaylend-gold-priobrela-poiskovye-aktivy-na-kamchatke/'],
   ['EastRussia', 'https://www.eastrussia.ru/news/kompaniya-khaylend-gold-priobrela-aktivy-na-kamchatke/']]),
 ('g15f35a5d',
  'src',
  [['РБК', 'https://www.rbc.ru/business/25/04/2025/680b35279a79473cf11967ae'],
   ['LEVEL Legal Services',
    'https://www.level-legal.com/news/yuridicheskaya-firma-level-legal-services-osushestvila-kompleksnoe-yuridicheskoe-konsultirovanie-chastnogo-investora-v-svyazi-s-priobreteniem-gk-zapadnaya'],
   ['BIRCH Legal', 'https://www.birchlegal.ru/services/sectors/energy_and_natural_resources/'],
   ['Abireg', 'https://abireg.ru/newsitem/106857/'],
   ['Золото и технологии',
    'https://zolteh.ru/news/gruppa_okto_priobrela_100_aktsiy_zolotodobyvayushchey_gk_zapadnaya/'],
   ['НедраДВ', 'https://nedradv.ru/nedradv/ru/page_industry?obj=49c37832e6138f440d05d2a5f676c230'],
   ['НедраДВ', 'https://nedradv.ru/nedradv/ru/page_news?obj=bd23184a4151a5d68908f0107dbffe35'],
   ['Золото и технологии', 'https://zolteh.ru/news/okto_zoloto_pereimenovalo_a_s_zapadnaya_v_gok_kedrovskiy/'],
   ['Коммерсантъ — «Сделки года»', 'https://www.kommersant.ru/doc/8077927']],
  [['РБК', 'https://www.rbc.ru/business/25/04/2025/680b35279a79473cf11967ae'],
   ['Золото и технологии',
    'https://zolteh.ru/news/gruppa_okto_priobrela_100_aktsiy_zolotodobyvayushchey_gk_zapadnaya/'],
   ['LEVEL Legal Services',
    'https://www.level-legal.com/news/yuridicheskaya-firma-level-legal-services-osushestvila-kompleksnoe-yuridicheskoe-konsultirovanie-chastnogo-investora-v-svyazi-s-priobreteniem-gk-zapadnaya'],
   ['Telegram — LawFirms (BIRCH)', 'https://t.me/LawFirms/8961'],
   ['Abireg', 'https://abireg.ru/newsitem/106857/'],
   ['Коммерсантъ — «Сделки года»', 'https://www.kommersant.ru/doc/8077927'],
   ['Золото и технологии', 'https://zolteh.ru/news/okto_zoloto_pereimenovalo_a_s_zapadnaya_v_gok_kedrovskiy/'],
   ['НедраДВ', 'https://nedradv.ru/nedradv/ru/page_industry?obj=49c37832e6138f440d05d2a5f676c230'],
   ['НедраДВ', 'https://nedradv.ru/nedradv/ru/page_news?obj=bd23184a4151a5d68908f0107dbffe35']]),
 ('gbc0b68bd',
  'src',
  [['Ведомости',
    'https://www.vedomosti.ru/business/articles/2025/04/21/1105538-faberlik-prodala-fabriku-po-poshivu-odezhdi'],
   ['Retail.ru',
    'https://www.retail.ru/news/kompaniya-faberlik-prodala-fabriku-po-poshivu-odezhdy-strukture-voentorga-21-aprelya-2025-263762/'],
   ['New Retail',
    'https://new-retail.ru/novosti/retail/faberlik_prodala_svoyu_shveynuyu_fabriku_v_ivanovskoy_oblasti/'],
   ['Sostav.ru',
    'https://www.sostav.ru/publication/faberlik-prodal-fabriku-po-poshivu-odezhdy-strukture-voentorga-74664.html']],
  [['Ведомости',
    'https://www.vedomosti.ru/business/articles/2025/04/21/1105538-faberlik-prodala-fabriku-po-poshivu-odezhdi'],
   ['Retail.ru',
    'https://www.retail.ru/news/kompaniya-faberlik-prodala-fabriku-po-poshivu-odezhdy-strukture-voentorga-21-aprelya-2025-263762/'],
   ['New Retail',
    'https://new-retail.ru/novosti/retail/faberlik_prodala_svoyu_shveynuyu_fabriku_v_ivanovskoy_oblasti/'],
   ['Sostav.ru',
    'https://www.sostav.ru/publication/faberlik-prodal-fabriku-po-poshivu-odezhdy-strukture-voentorga-74664.html']]),
 ('g181d7687',
  'src',
  [['РБК', 'https://www.rbc.ru/technology_and_media/04/02/2025/67a1ecc09a7947034c102e35'],
   ['ComNews', 'https://www.comnews.ru/content/237587/2025-02-05/2025-w06/1007/yadro-priobrela-38-doley-kb-borey'],
   ['CNews', 'https://www.cnews.ru/news/top/2025-02-04_yadro_zajmetsya_sozdaniem_produktov'],
   ['Интерфакс', 'https://www.interfax.ru/business/1006209'],
   ['РБК Компании', 'https://companies.rbc.ru/id/5177746194577-ooo-konstruktorskoe-byuro-borej/'],
   ['CNews', 'https://www.cnews.ru/news/line/2026-07-24_yadro_predstavila_kompleksnoe']],
  [['РБК', 'https://www.rbc.ru/technology_and_media/04/02/2025/67a1ecc09a7947034c102e35'],
   ['Интерфакс', 'https://www.interfax.ru/business/1006209'],
   ['ComNews', 'https://www.comnews.ru/content/237587/2025-02-05/2025-w06/1007/yadro-priobrela-38-doley-kb-borey'],
   ['ЕГРЮЛ', 'https://projectcompass.ru/api/companies/g8f46008e/fns'],
   ['CNews', 'https://www.cnews.ru/news/top/2025-02-04_yadro_zajmetsya_sozdaniem_produktov'],
   ['РБК Компании', 'https://companies.rbc.ru/id/5177746194577-ooo-konstruktorskoe-byuro-borej/'],
   ['CNews', 'https://www.cnews.ru/news/line/2026-07-24_yadro_predstavila_kompleksnoe']]),
 ('g57b3b93c',
  'events.0.note',
  'Лесопромышленный холдинг «Свеза» купил две промышленные площадки в Ленобласти и одну в Пскове по производству '
  'картона и бумаги. До 2022 года эти активы принадлежали структурам австрийского холдинга Mayr-Melnhof, затем в '
  'течение двух лет предприятиями владел строительный холдинг «Гранель». Стороны подписали договор купли-продажи; '
  'сделку одобрила Федеральная антимонопольная служба. Сумму и условия сделки в «Свезе» не раскрывают.',
  '«Свеза» купила три предприятия по выпуску бумаги и картона: «ММПОФ Пэкэджинг» и «ММПОФ Ротогравюр» в '
  'Ломоносовском районе Ленинградской области и «Невские грани» в Пскове. Первые два до 2022 года принадлежали '
  'Mayr-Melnhof, «Невские грани» — австрийской Tannpapier; в декабре 2022 года все три перешли к «Гранели», в марте '
  '2023 года — к ООО «Форвард», которое и купила «Свеза». Сделку одобрила ФАС; сумму «Свеза» не раскрывает.'),
 ('ga0a49202',
  'events.0.note',
  'Ранее рассматривалась продажа МТС Live и Яндексу, но переговоры с МТС в итоге не привели к сделке — стороны не '
  'сошлись в цене и условиях.',
  'Сеть начала искать покупателя. По неофициальным данным, в 2023 году шли переговоры о продаже «МТС Энтертеймент» '
  '(теперь МТС Live), но стороны не договорились о цене.')]

_RETRACT = [('g1059432d', 'sum', '€220 млн'),
 ('gc677124b', 'sum', '$29 млн'),
 ('gfa14411d', 'seller', 'ООО «РЕ Трэйдинг», LPP SA'),
 ('g94683ed2', 'seller', 'Акционеры Рив Гош')]

_NOTES = [('g15f35a5d',
  'no_profile.seller',
  'Продавцы — менеджмент группы (65,41% акций МКАО «Западная Голд Майнинг Лимитед») и миноритарии (9,53%), еще '
  '25,06% — казначейский пакет (РБК; LEVEL Legal Services: «у менеджмента и миноритариев»; BIRCH — консультант '
  '«акционеров МКАО»). Имена продающих акционеров не названы ни в одном источнике: РБК, «Золото и технологии», '
  'Абирег, LEVEL Legal Services, BIRCH (Telegram LawFirms), «Коммерсантъ» («Сделки года»); реестр акционеров МКАО '
  'открыто не публикуется.'),
 ('gbc0b68bd',
  'no_profile.asset',
  'ИНН ООО «Фэшн фэктори» не найден: веб-поиск по имени и «Фаберлику», datanewton.ru, companies.rbc.ru — совпадений '
  'с ивановской фабрикой нет; в статьях (Ведомости, Retail.ru, New Retail, Sostav) ИНН не назван. Предмет записан '
  'текстом.')]

_COMPANY = [('g03e5be54', 'name', 'LPP Group Rus (Reserved, Cropp, House, Mohito, Sinsay)', 'РЕ Трэйдинг'),
 ('g03e5be54',
  'desc',
  'Российская сеть магазинов польской LPP Group под брендами Reserved, Cropp, House, Mohito, Sinsay.',
  'Российская компания польской LPP, управлявшая магазинами Reserved, Cropp, House, Mohito и Sinsay; в 2022 году 95% '
  'перешли к Far East Services FZCO из Дубая, 5% — гендиректору Анне Пилюгиной.'),
 ('g7f6433d2', 'ind', 'Химия и удобрения', 'Производство тары'),
 ('g4b079e80',
  'desc',
  'Турецкий производитель бытовой техники, купивший российские активы Whirlpool (завод в Липецке, бренды Hotpoint и '
  'Indesit) в 2022 году за €220 млн.',
  'Турецкий производитель бытовой техники (марки Beko, Blomberg); в 2022 году купил российский бизнес Whirlpool — '
  'заводы в Липецке и права на бренды Indesit, Hotpoint и Stinol в России.'),
 ('g73bb8426',
  'desc',
  'Покупатель российских заводов MM Packaging (Mayr-Melnhof Group) в Санкт-Петербурге и Пскове.',
  'Московская девелоперская группа «Гранель»; в декабре 2022 года купила российские упаковочные заводы австрийской '
  'Mayr-Melnhof.'),
 ('g849d19d0',
  'desc',
  'ООО с лицензиями на месторождения золота и серебра на Камчатке (участки «Кларин» и «Нимаевский»); в 2025 году его '
  'купила Highland Gold у Андрея Комарова (экс-владельца ЧТПЗ).',
  'ООО с лицензиями на геологическое изучение участков «Кларин» и «Нимаевский» на Камчатке (золото и серебро); с '
  'июня 2025 года принадлежит структуре Highland Gold.'),
 ('g2bda5372',
  'desc',
  'Компания по пошиву военного обмундирования для Минобороны и МЧС; в 2025 году купила у «Фаберлик» фабрику одежды '
  '«Фэшн фэктри» в Ивановской области за 150 млн ₽.',
  'Шьет форму для Минобороны и МЧС, у компании шесть фабрик в Карачаево-Черкесии и Кабардино-Балкарии; 26% '
  'принадлежат АО «Военторг».'),
 ('g8f46008e',
  'desc',
  'Компания, 38% которой в 2025 году купила «КНС Групп» (Yadro) за 100 млн ₽.',
  'Разработчик и производитель систем охлаждения для центров обработки данных (бренд BOREY), Москва; с 2025 года 38% '
  'принадлежат «КНС Групп» (Yadro).'),
 ('g66a64a9f',
  'desc',
  'ИТ-компания (ООО «Авара Ай Ти Солюшенс»): по данным ЕГРЮЛ, ее акционерами были Александр Ермаков (56%), Юрий '
  'Шумаков (30%) и Александр Пирогов (14%), выручка за 2021 год — 297 млн ₽. В 2022 году, купив российский бизнес '
  'SoftwareONE, образовала мультивендорную ИТ-компанию полного цикла под брендом WONE IT (сейчас — ООО «Ван Ай Ти '
  'Трейд», Wone IT).',
  'ИТ-интегратор (ООО «Ван Ай Ти Солюшенс», ранее «Авара Ай Ти Солюшенс»); в 2022 году его совладельцы Александр '
  'Ермаков и Юрий Шумаков купили российский бизнес SoftwareONE.'),
 ('gd1fce9cc', 'legal_short', None, 'АО ГРК «Западная»'),
 ('g6eb3c726',
  'desc',
  'Купила в 2025 году сеть квестов «Клаустрофобия» (169 локаций, товарные знаки, права аренды) — точная сумма не '
  'раскрыта; по экспертной оценке, сеть стоит 400–500 млн ₽.',
  'Сеть квестов и перформансов, основана в 2015 году и начинала с хоррор-квестов; среди ее квестов — «Амитивилль» на '
  'ВДНХ, «БШ2: Электрозавод» и «Дом Беллы».'),
 ('g6eb3c726', 'ind', 'Медиа', 'Развлечения'),
 ('g6eb3c726',
  'ownership',
  [{'name': 'Вадим Змовик',
    'id': None,
    'share': '51%',
    'as_of': '2025-07',
    'source': ['РБК', 'https://www.rbc.ru/technology_and_media/15/08/2025/689db55a9a7947b058474799']},
   {'name': 'Павел Вараксин',
    'id': None,
    'share': '33%',
    'as_of': '2025-07',
    'source': ['РБК', 'https://www.rbc.ru/technology_and_media/15/08/2025/689db55a9a7947b058474799']},
   {'name': 'Евгений Авин (Антонов)',
    'id': None,
    'share': '16%',
    'as_of': '2025-07',
    'source': ['РБК', 'https://www.rbc.ru/technology_and_media/15/08/2025/689db55a9a7947b058474799']}],
  None),
 ('g8fd0df01',
  'desc',
  'Сеть квестов (169 активных локаций, оборот 1–1,1 млрд ₽); в 2025 году ее купил GrimTeam за 400 млн ₽.',
  'Крупнейшая в России сеть квестов, основана в 2013 году; на 2024 год — 37 точек и 169 активных квестов.'),
 ('g8fd0df01', 'ind', 'Медиа', 'Развлечения'),
 ('g03e5be54', 'legal_short', None, 'ООО «РЕ Трэйдинг»'),
 ('g4de3e3ed', 'legal_short', None, 'ООО «Дэнир»'),
 ('g54913880', 'legal_short', None, 'ООО «Виола»'),
 ('g73bb8426', 'legal_short', None, 'ООО «ГК "гранель»'),
 ('g13d18a65', 'legal_short', None, 'АО «АЙ ЭЙЧ ПИ Апплаенсес»'),
 ('ge90270b7', 'legal_short', None, 'ООО «ВАН АЙ ТИ Трейд»'),
 ('g69b9ab00', 'legal_short', None, 'ООО «АГК»'),
 ('g842a7fd2', 'legal_short', None, 'ООО «Аромалюкс»'),
 ('gb0536c82', 'legal_short', None, 'ООО «Гиперспэйс»'),
 ('g849d19d0', 'legal_short', None, 'ООО «Гейзер Голд»'),
 ('g51ad562a', 'legal_short', None, 'АО «Группа ОКТО»'),
 ('g2bda5372', 'legal_short', None, 'ООО «Воентекстильпром»'),
 ('g2e17f275', 'legal_short', None, 'АО «Фаберлик»'),
 ('g8f46008e', 'legal_short', None, 'ООО «КБ БОРЕЙ»')]

_TOUCHED = [('g1059432d', 'date'),
 ('g1059432d', 'eco.context'),
 ('g1059432d', 'eco.rationale'),
 ('g1059432d', 'eco.share'),
 ('g1059432d', 'eco.sum'),
 ('g1059432d', 'eco.val'),
 ('g1059432d', 'extra'),
 ('g1059432d', 'law.struct'),
 ('g1059432d', 'law.terms'),
 ('g1059432d', 'src'),
 ('g1059432d', 'sum'),
 ('g1059432d', 'title'),
 ('g15f35a5d', 'eco.context'),
 ('g15f35a5d', 'eco.fin'),
 ('g15f35a5d', 'eco.rationale'),
 ('g15f35a5d', 'eco.share'),
 ('g15f35a5d', 'eco.sum'),
 ('g15f35a5d', 'eco.target_fin'),
 ('g15f35a5d', 'eco.val'),
 ('g15f35a5d', 'extra'),
 ('g15f35a5d', 'law.appr'),
 ('g15f35a5d', 'law.struct'),
 ('g15f35a5d', 'src'),
 ('g15f35a5d', 'sum'),
 ('g181d7687', 'eco.context'),
 ('g181d7687', 'eco.rationale'),
 ('g181d7687', 'eco.share'),
 ('g181d7687', 'eco.sum'),
 ('g181d7687', 'eco.target_fin'),
 ('g181d7687', 'eco.val'),
 ('g181d7687', 'law.adv'),
 ('g181d7687', 'law.struct'),
 ('g181d7687', 'src'),
 ('g181d7687', 'sum'),
 ('g181d7687', 'title'),
 ('g55f1c662', 'date'),
 ('g55f1c662', 'eco.context'),
 ('g55f1c662', 'eco.share'),
 ('g55f1c662', 'eco.target_fin'),
 ('g55f1c662', 'extra'),
 ('g55f1c662', 'law.struct'),
 ('g55f1c662', 'law.terms'),
 ('g55f1c662', 'src'),
 ('g55f1c662', 'title'),
 ('g57b3b93c', 'date'),
 ('g57b3b93c', 'eco.context'),
 ('g57b3b93c', 'eco.rationale'),
 ('g57b3b93c', 'eco.share'),
 ('g57b3b93c', 'eco.target_fin'),
 ('g57b3b93c', 'extra'),
 ('g57b3b93c', 'src'),
 ('g57b3b93c', 'title'),
 ('g94683ed2', 'eco.context'),
 ('g94683ed2', 'eco.rationale'),
 ('g94683ed2', 'eco.share'),
 ('g94683ed2', 'eco.sum'),
 ('g94683ed2', 'eco.target_fin'),
 ('g94683ed2', 'eco.val'),
 ('g94683ed2', 'extra'),
 ('g94683ed2', 'law.terms'),
 ('g94683ed2', 'seller'),
 ('g94683ed2', 'src'),
 ('g94683ed2', 'sum'),
 ('g94683ed2', 'title'),
 ('ga0a49202', 'buyer'),
 ('ga0a49202', 'buyer_name'),
 ('ga0a49202', 'date'),
 ('ga0a49202', 'eco.context'),
 ('ga0a49202', 'eco.share'),
 ('ga0a49202', 'eco.sum'),
 ('ga0a49202', 'eco.val'),
 ('ga0a49202', 'extra'),
 ('ga0a49202', 'law.adv'),
 ('ga0a49202', 'law.terms'),
 ('ga0a49202', 'src'),
 ('ga0a49202', 'sum'),
 ('ga0a49202', 'title'),
 ('gbc0b68bd', 'asset'),
 ('gbc0b68bd', 'eco.context'),
 ('gbc0b68bd', 'eco.share'),
 ('gbc0b68bd', 'eco.sum'),
 ('gbc0b68bd', 'extra'),
 ('gbc0b68bd', 'law.adv'),
 ('gbc0b68bd', 'src'),
 ('gbc0b68bd', 'sum'),
 ('gbc0b68bd', 'title'),
 ('gc677124b', 'date'),
 ('gc677124b', 'eco.context'),
 ('gc677124b', 'eco.share'),
 ('gc677124b', 'eco.sum'),
 ('gc677124b', 'eco.target_fin'),
 ('gc677124b', 'eco.val'),
 ('gc677124b', 'extra'),
 ('gc677124b', 'law.appr'),
 ('gc677124b', 'law.terms'),
 ('gc677124b', 'src'),
 ('gc677124b', 'sum'),
 ('gc677124b', 'title'),
 ('gd88cbe9a', 'eco.context'),
 ('gd88cbe9a', 'eco.rationale'),
 ('gd88cbe9a', 'eco.val'),
 ('gd88cbe9a', 'extra'),
 ('gd88cbe9a', 'law.adv'),
 ('gd88cbe9a', 'law.struct'),
 ('gd88cbe9a', 'src'),
 ('gd88cbe9a', 'title'),
 ('gfa14411d', 'date'),
 ('gfa14411d', 'eco.context'),
 ('gfa14411d', 'eco.rationale'),
 ('gfa14411d', 'eco.share'),
 ('gfa14411d', 'eco.val'),
 ('gfa14411d', 'extra'),
 ('gfa14411d', 'law.adv'),
 ('gfa14411d', 'law.terms'),
 ('gfa14411d', 'seller'),
 ('gfa14411d', 'src'),
 ('gfa14411d', 'title'),
 ('gfc7e5649', 'buyer'),
 ('gfc7e5649', 'buyer_name'),
 ('gfc7e5649', 'date'),
 ('gfc7e5649', 'eco.context'),
 ('gfc7e5649', 'eco.rationale'),
 ('gfc7e5649', 'eco.share'),
 ('gfc7e5649', 'eco.target_fin'),
 ('gfc7e5649', 'extra'),
 ('gfc7e5649', 'law.adv'),
 ('gfc7e5649', 'law.struct'),
 ('gfc7e5649', 'law.terms'),
 ('gfc7e5649', 'src'),
 ('gfc7e5649', 'title')]

PROSE = ('extra', 'eco.share', 'eco.val', 'eco.target_fin', 'eco.fin', 'eco.rationale', 'eco.context',
         'law.struct', 'law.terms', 'law.appr')


def _get(obj, field):
    for p in field.split('.'):
        if isinstance(obj, list):
            obj = obj[int(p)] if p.isdigit() and int(p) < len(obj) else None
        else:
            obj = obj.get(p) if isinstance(obj, dict) else None
    return obj


def _set(obj, field, value):
    parts = field.split('.')
    for p in parts[:-1]:
        obj = obj[int(p)] if isinstance(obj, list) else obj.setdefault(p, {})
    if isinstance(obj, list):
        obj[int(parts[-1])] = value
    elif value is None:
        obj.pop(parts[-1], None)
    else:
        obj[parts[-1]] = value


def _apply(data):
    import fact_edit_guard
    import review
    deals = {d['id']: d for d in data['deals']}
    done = 0
    for cid, field, old, new, quote, url in ONE_OFF:
        card = deals[cid]
        cur = _get(card, field)
        if cur == new:
            continue                                   # уже применено
        assert cur == old, (cid, field, cur)
        _set(card, field, new)
        if field in fact_edit_guard.FACT_FIELDS:
            fact_edit_guard.log(card, field, new, quote, url, _BY)
        done += 1
    for cid, field, old, new in _SET:
        cur = _get(deals[cid], field)
        if cur == new:
            continue
        assert cur == old, (cid, field, cur)
        _set(deals[cid], field, new)
        done += 1
    for cid, field, value in _RETRACT:
        lst = deals[cid].setdefault('retracted', {}).setdefault(field, [])
        if value not in lst:
            lst.append(value)
    for cid, path, value in _NOTES:
        notes = deals[cid].setdefault('accepted_notes', {})
        if _get(notes, path) == value:
            continue
        assert _get(notes, path) is None, (cid, path, _get(notes, path))
        _set(notes, path, value)
    for comp, field, old, new in _COMPANY:
        c = data['companies'][comp]
        if c.get(field) == new:
            continue
        assert c.get(field) == old, (comp, field, c.get(field))
        if new is None:
            c.pop(field, None)
        else:
            c[field] = new
    # Прежние записи таблицы правок на тронутые поля: отпечаток их `new` — в proofread_absorbed,
    # иначе already_applied() сочтет их невыполненными (docs/card_editing.md, «Таблица FIXES»).
    for cid, field in _TOUCHED:
        card = deals[cid]
        for f in review.FIXES:
            if (f['id'], f['field']) != (cid, field):
                continue
            if field == 'src':
                if not review.already_applied(f, card, data.get('companies')):
                    marks = card.setdefault('proofread_absorbed', {}).setdefault('src', [])
                    fp = review.fix_fingerprint(f['new'][1])
                    if fp not in marks:
                        marks.append(fp)
                continue
            if f['new'] is None or f['new'] == _get(card, field):
                continue
            marks = card.setdefault('proofread_absorbed', {}).setdefault(field, [])
            fp = review.fix_fingerprint(f['new'])
            if fp not in marks:
                marks.append(fp)
    return done


def _self_check():
    """Проза — по цитате (числа, дословность, правила текста): то же, что review.py спросил бы у записи таблицы."""
    from prose_gate import prose_problems
    bad = 0
    for cid, field, old, new, quote, url in ONE_OFF:
        if field in PROSE and isinstance(new, str) and new.strip() not in ('', '—'):
            for p in prose_problems(new, quote, field):
                print('  %s %s: %s' % (cid, field, p))
                bad += 1
    return bad


if __name__ == '__main__':
    import mass_edit_guard  # noqa: E402
    data = json.load(open(DATA, encoding='utf-8'))
    before = copy.deepcopy(data)
    n = _apply(data)
    mass_edit_guard.check(before, data, os.environ.get('MASS_OK'))
    print('Разовая часть m002: изменений %d — проверки пройдены.' % n)
    if '--write' in sys.argv:
        fresh = json.load(open(DATA, encoding='utf-8'))      # перечитать прямо перед записью
        before = copy.deepcopy(fresh)
        _apply(fresh)
        mass_edit_guard.check(before, fresh, os.environ.get('MASS_OK'))
        with open(DATA, 'w', encoding='utf-8') as fh:
            json.dump(fresh, fh, ensure_ascii=False, indent=1)
        print('Записано.')
    else:
        print('Замечаний к прозе: %d' % _self_check())
        print('Сухой прогон. Запись — с ключом --write.')
