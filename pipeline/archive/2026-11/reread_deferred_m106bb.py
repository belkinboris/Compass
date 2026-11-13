# -*- coding: utf-8 -*-
"""Вычитка 13 ноября 2026, партия m106b (часть 2): последние отложенные случаи марафона.

g26608f96 (Махмудов / «Аквариус», июнь 2025): Махмудова называли возможным покупателем 51% (CNews, три
  источника); актив в августе 2025 года ушел S8 Capital и «МТ-Интеграции» (своя карточка g139db8c2).
  Это карточка-предвестник: статус «Не состоялась» остается, карточка не сливается
  (docs/card_status_dates.md, «Карточка-предвестник и поздняя судьба актива»). 40–55 млрд ₽ — оценка
  гендиректора «Инвенторуса» Евгения Елфимова, не цена; дата — день статьи CNews 3 июня 2025 года;
  заголовок — по стандарту для несостоявшейся покупки; проза — версии с атрибуцией.
g1b5e8ab8 (RBI, октябрь 2025): попытка продать долю российского Райффайзенбанка местному покупателю
  не удалась, по неофициальным данным — из-за позиции российских властей (Reuters в перепечатке Daily Sabah).
  Статус «Не состоялась» относится к этой попытке; заголовок — по стандарту; иск к Rasperia и смена
  гендиректора RBI — другие сюжеты, сняты вместе с их источниками; 7 млрд € прибыли — не оценка, в контекст.
ce6b8c447 (Carlsberg / «Балтика»): по Интерфаксу (источник), 71 млрд ₽ — цена «Балтики» в рамочном
  соглашении с «Арнестом» («более 71 млрд рублей»), а не сумма иска о компенсации. Сумма — «Более 71 млрд ₽»,
  sum_basis lower_bound; строка золотой выборки — те же факты (docs/analytics_acceptance.md, «Правка
  карточки золотой выборки»): заголовок и доля карточки не меняются, отпечаток доли цел.
g82725e96 («Петровакс»): покупатель по ЕГРЮЛ — ООО «Фарминвест» (верно по docs/card_parties.md), но заголовок
  называет тех, кто за ним стоит, понятно читателю, а «Как устроена сделка» начинается с них (Интерфакс).
g74c84c09 («Фрутоняня»): Алексей Мельник — контролирующий акционер по отчетности «Прогресса» за 2024 год
  (Ведомости), Лисин — только по неофициальным данным (Коммерсантъ): покупатель остается; «цель» без
  автора снята, версия о Лисине в «Дополнительно» — как версия.

Без ключа — сухой прогон; --write перечитывает базу прямо перед записью; повтор — «Уже применено».

    python3 pipeline/archive/2026-11/reread_deferred_m106bb.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
DISCREP = os.path.join(ROOT, 'pipeline', 'facts_discrepancies.json')
SIGNALS = os.path.join(ROOT, 'static', 'data', 'signals.json')
BY, DAY = 'reread_deferred_m106bb', '2026-11-13'
GOLD = os.path.join(ROOT, 'pipeline', 'gold', 'analytics_gold.json')
A = '__ABSENT__'
RETRACT = ('sum', 'status', 'buyer_name', 'asset', 'seller')

A_ = A
MERGES = []

# (карточка, поле, старое значение, новое значение, цитата, адрес, флаги).
OPS = [('g26608f96',
  'title',
  'Искандер Махмудов вел переговоры о покупке контроля в ГК «Аквариус» — сделка не состоялась',
  'Искандер Махмудов не купил контроль в «Аквариусе»',
  'Возможным покупателем 51% доли компании собседники CNews называют Искандера Махмудова',
  'https://www.cnews.ru/news/top/2025-06-03_na_rynke_gotovitsya_krupnaya',
  ''),
 ('g26608f96',
  'date',
  '2025-06-01',
  '2025-06-03',
  'Как сообщили три источника CNews, знакомые со сделкой, она состоится в июне 2025 г. (статья 3 июня 2025 года)',
  'https://www.cnews.ru/news/top/2025-06-03_na_rynke_gotovitsya_krupnaya',
  ''),
 ('g26608f96',
  'sum',
  '40–55 млрд ₽ (по оценке)',
  'Не раскрыта',
  'Итого, стоимость доли в компании может уйти за 45-55 миллиардов рублей — оценка эксперта, не цена',
  'https://www.cnews.ru/news/top/2025-06-03_na_rynke_gotovitsya_krupnaya',
  ''),
 ('g26608f96',
  'eco.sum',
  '40–55 млрд ₽ (по оценке)',
  'Не раскрыта',
  'Итого, стоимость доли в компании может уйти за 45-55 миллиардов рублей',
  'https://www.cnews.ru/news/top/2025-06-03_na_rynke_gotovitsya_krupnaya',
  ''),
 ('g26608f96',
  'eco.share',
  'Искандер Махмудов через свои структуры вел переговоры о приобретении 51% акционерного капитала ГК «Аквариус» '
  '(сделка не состоялась).',
  '51% акций АО «Группа Аквариус»',
  'Возможным покупателем 51% доли компании собседники CNews называют Искандера Махмудова',
  'https://www.cnews.ru/news/top/2025-06-03_na_rynke_gotovitsya_krupnaya',
  ''),
 ('g26608f96',
  'eco.val',
  'С учетом роста мощностей — в Твери запущен комплекс — и доли на рынке серверов до 75% в корпоративном сегменте '
  'текущая оценка компании может достигать 90–100 млрд ₽. Тогда базовая стоимость 51% составит порядка 40 млрд ₽, '
  'а с премией 20–30% за контрольный пакет — 45–55 миллиардов ₽.',
  'Гендиректор компании «Инвенторус» Евгений Елфимов оценивал весь «Аквариус» в 90–100 млрд ₽, базовую стоимость '
  '51% — примерно в 40 млрд ₽, а с премией 20–30% за контрольный пакет — в 45–55 млрд ₽.',
  'текущая оценка может достигать 90–100 млрд рублей, — продолжает он. — Итого, базовая стоимость 51% компании '
  'составит порядка 40 млрд рублей.',
  'https://www.cnews.ru/news/top/2025-06-03_na_rynke_gotovitsya_krupnaya',
  ''),
 ('g26608f96',
  'extra',
  'Стороны ведут переговоры: Махмудов через свои структуры приобретает 51% акционерного капитала ГК «Аквариус». '
  'Эксперты оценивают этот пакет в 40–55 млрд ₽ при условии Net debt = 0.',
  'В июне 2025 года, по неофициальным данным, возможным покупателем 51% «Аквариуса» называли Искандера Махмудова; '
  'по другой версии, актив могли купить УГМК или Трансмашхолдинг, в число владельцев которых он входит. До сделки '
  'дело не дошло: в августе 2025 года покупателями 79% «Аквариуса» назвали S8 Capital и ГК «МТ-Интеграция».',
  '',
  '',
  ''),
 ('g26608f96',
  'eco.context',
  'В ноябре 2024 года «СберИнвест», входящий в блок корпоративно-инвестиционного бизнеса Сбербанка, получил 12% в '
  'капитале «Аквариуса», а позже, по неофициальным данным, докупил еще 12% — сейчас у него 24%. Крупными долями '
  '«Аквариуса» владеют также Алексей Калинин и президент одноименной группы Владимир Степанов. О возможной '
  'продаже доли говорили еще в июне 2025 года, но тогда назывались другие потенциальные инвесторы — Уральская '
  'горно-металлургическая компания (УГМК) и Трансмашхолдинг (ТМХ); в число владельцев обеих входит Искандер '
  'Махмудов. К августу 2025 года вместо Махмудова покупателем называли S8 Capital и ГК «МТ-Интеграция», но связь '
  'между двумя версиями ни разу не подтверждена. Основатель реального покупателя, S8 Capital, публично назван: '
  '«Инвестиционный холдинг S8 Capital Армена Саркисяна» (Sostav.ru, 22.08.2025) — Махмудов ни в этой, ни в других '
  'публикациях о финальной сделке не фигурирует. Реальным покупателем стал альянс S8 Capital и ГК «МТ-Интеграция» '
  '(79% акций, август 2025 года) — этой сделке посвящена отдельная карточка на сайте.',
  'В ноябре 2024 года «СберИнвест» из группы Сбербанка получил 12% «Аквариуса», а позже, по неофициальным данным, '
  'еще 12%; крупными долями владели также Алексей Калинин и президент группы Владимир Степанов. По неофициальным '
  'данным, у компании был большой кассовый разрыв. Глава совета директоров «Аквариуса» Алексей Калинин, ТМХ и '
  'УГМК на вопросы о сделке не ответили.\n'
  '\n'
  'В августе 2025 года, по неофициальным данным, 79% «Аквариуса» собрались выкупить S8 Capital Армена Саркисяна и '
  'ГК «МТ-Интеграция»; «МТ-Интеграция» свое участие опровергла.',
  'Глава совета директоров «Аквариуса» Алексей Калинин не ответил на вопросы CNews относительно сделки, как и '
  'представители ТМХ и УГМК.',
  'https://www.cnews.ru/news/top/2025-06-03_na_rynke_gotovitsya_krupnaya',
  ''),
 ('g1b5e8ab8',
  'title',
  'Raiffeisen Bank International попытался продать долю в российском бизнесе',
  'RBI не продал долю в российском Райффайзенбанке',
  'Raiffeisen Bank International (RBI) has reportedly failed in another attempt to sell a stake in its Russian '
  'business',
  'https://www.dailysabah.com/business/economy/raiffeisen-fails-in-new-attempt-to-sell-stake-in-russia-sources/amp',
  ''),
 ('g1b5e8ab8',
  'asset',
  A,
  'АО «Райффайзенбанк»',
  'Raiffeisen has been looking to sell a stake in its Russian arm to a local buyer',
  'https://www.dailysabah.com/business/economy/raiffeisen-fails-in-new-attempt-to-sell-stake-in-russia-sources/amp',
  ''),
 ('g1b5e8ab8',
  'eco.share',
  '—',
  'Доля в АО «Райффайзенбанк»',
  'Raiffeisen has been looking to sell a stake in its Russian arm to a local buyer',
  'https://www.dailysabah.com/business/economy/raiffeisen-fails-in-new-attempt-to-sell-stake-in-russia-sources/amp',
  ''),
 ('g1b5e8ab8',
  'eco.val',
  'Особый статус Raiffeisen и его размер — гораздо больший, чем у других европейских банков в России, '
  'итальянского UniCredit и меньшей венгерской группы OTP Bank, — позволили RBI накопить там около 7 млрд евро '
  '($8,22 млрд) прибыли, которая теперь заблокирована.',
  '—',
  '',
  '',
  ''),
 ('g1b5e8ab8',
  'law.struct',
  'По неофициальным данным, RBI снова не смогла продать долю в российском бизнесе. Эта попытка была не первой.',
  'По неофициальным данным, RBI пытался продать долю в российском Райффайзенбанке местному покупателю, '
  'рассчитывая, что Москва снимет запрет на вывод из России прибыли этого бизнеса, но российские власти продажу '
  'не поддержали. Попытка была не первой: продать долю раньше не раз пытался гендиректор RBI Йохан Штробль, по '
  'неофициальным данным, он ради этого приезжал в Россию.',
  'Chief Executive Johann Strobl had made several attempts in the past to sell a stake in the Russian business. '
  'The first person said he had visited Russia for this end.',
  'https://www.dailysabah.com/business/economy/raiffeisen-fails-in-new-attempt-to-sell-stake-in-russia-sources/amp',
  ''),
 ('g1b5e8ab8',
  'law.appr',
  'По заявлению представителя Raiffeisen, банк сокращает бизнес в России, а любая продажа его бизнеса требует '
  'одобрения Москвы. Raiffeisen Bank International вел переговоры о продаже своей российской дочерней компании, '
  'но не мог назвать сроки: требовались многочисленные регуляторные разрешения, в том числе от российских '
  'властей.',
  'По словам представителя RBI, для продажи нужны многочисленные разрешения регуляторов, в том числе российских '
  'властей; по неофициальным данным, российские чиновники продажу не поддержали.',
  '"as numerous regulatory approvals are required, including approvals of the Russian authorities."',
  'https://www.dailysabah.com/business/economy/raiffeisen-fails-in-new-attempt-to-sell-stake-in-russia-sources/amp',
  ''),
 ('g1b5e8ab8',
  'eco.context',
  'Raiffeisen проводит платежи по газопроводу «Турецкий поток» — единственному оставшемуся у России маршруту '
  'поставок газа в Европу после того, как остальные были перекрыты. За первые восемь месяцев этого года по '
  '«Турецкому потоку» через Турцию в европейские страны, включая Болгарию и Венгрию, было поставлено около 11,5 '
  'млрд куб. м газа. По средним рыночным ценам этот газ стоил примерно $3,8 млрд — существенная часть российского '
  'газового экспорта. 17 декабря 2025 года наблюдательный совет RBI назначил Михаэля Хеллерера преемником Йохана '
  'Штробля на посту CEO с 1 июля 2026 года; именно Штробль лично вел провалившиеся переговоры о продаже и решил '
  'не добиваться продления своего мандата, который истекает в феврале 2027 года. В августе 2026 года RBI и его '
  'российская дочерняя структура АО «Райффайзенбанк» подали в венский суд иск на 3,15 млрд евро к российской '
  'Rasperia Trading Limited, впервые в мире применив статью 11a 14-го пакета санкций ЕС. Предмет взыскания — 28,5 '
  'млн акций STRABAG SE, замороженные на счете Rasperia в Австрии, вместе с накопленными дивидендами и выплатами '
  'от снижения капитала STRABAG. Российский суд наложил на RBI всемирный запрет на судебные разбирательства по '
  'этому делу, но прямо исключил из-под запрета разбирательство в Австрии; в начале августа 2026 года Rasperia '
  'отозвала оставшиеся иски в России. Разбирательство в Вене может занять около полугода, расходы RBI по делу '
  'оцениваются до 150 млн евро за 2026 год.',
  'По неофициальным данным, российские чиновники выступили против продажи, в том числе опасаясь, что покупка доли '
  'российским инвестором обернется западными санкциями против RBI; Москва хочет сохранить банк как канал платежей '
  'с Европой. Российский Райффайзенбанк — крупнейший банк в стране, не попавший под санкции, и он проводит '
  'платежи по газопроводу «Турецкий поток». В России у RBI скопилось около 7 млрд € прибыли, которую нельзя '
  'вывести.\n'
  '\n'
  'Представитель Raiffeisen сказал, что банк сокращает бизнес в России и ведет переговоры о продаже российской '
  '«дочки», но сроков назвать не может. ЦБ отказался комментировать переговоры с конкретными банками.',
  'Russian officials opposed a sale in part because they were concerned that a Russian buyer taking the stake '
  'could result in Western sanctions against RBI, the first person said.',
  'https://www.dailysabah.com/business/economy/raiffeisen-fails-in-new-attempt-to-sell-stake-in-russia-sources/amp',
  ''),
 ('g1b5e8ab8',
  'extra',
  'RBI не удалось продать долю в российской дочерней структуре. Переговоры лично вел председатель правления '
  'Johann Strobl. Продажа требует одобрения российских регуляторов.',
  'По неофициальным данным, в 2025 году RBI снова не смог продать долю в российском Райффайзенбанке: российские '
  'власти были против.',
  '',
  '',
  ''),
 ('g1b5e8ab8',
  'src',
  [['Reuters',
    'https://www.reuters.com/business/finance/austrias-raiffeisen-fails-new-effort-sell-stake-russia-sources-say-2025-10-01/'],
   ['Интерфакс', 'https://www.interfax.ru/business/1070262'],
   ['EQS-News (17.12.2025)',
    'https://www.eqs-news.com/news/ad-hoc/raiffeisen-bank-international-ag-michael-hollerer-will-succeed-johann-strobl-as-ceo-of-rbi-on-1-july-2026/7159e11d-5ea2-48ad-a80e-50265dbee62b_en'],
   ['Vindobona (09.08.2026)',
    'https://www.vindobona.org/article/landmark-3-15-billion-lawsuit-austrian-rbi-sues-russian-rasperia-in-a-vienna-court']],
  [['Reuters',
    'https://www.reuters.com/business/finance/austrias-raiffeisen-fails-new-effort-sell-stake-russia-sources-say-2025-10-01/'],
   ['Daily Sabah (перепечатка Reuters)',
    'https://www.dailysabah.com/business/economy/raiffeisen-fails-in-new-attempt-to-sell-stake-in-russia-sources/amp'],
   ['Интерфакс', 'https://www.interfax.ru/business/1070262']],
  'источники об этой попытке продажи; EQS (смена гендиректора) и Vindobona (иск к Rasperia) — о другом',
  'https://www.dailysabah.com/business/economy/raiffeisen-fails-in-new-attempt-to-sell-stake-in-russia-sources/amp',
  ''),
 ('ce6b8c447',
  'sum',
  '71 млрд ₽',
  'Более 71 млрд ₽',
  'За "Балтику" же, даже с учетом обязательного для сделок "на выход" 50%-ного дисконта, была установлена гораздо '
  'более существенная цена - более 71 млрд рублей, говорит источник.',
  'https://www.interfax.ru/russia/929541',
  ''),
 ('ce6b8c447',
  'eco.sum',
  '71 млрд ₽',
  'Более 71 млрд ₽',
  'была установлена гораздо более существенная цена - более 71 млрд рублей, говорит источник.',
  'https://www.interfax.ru/russia/929541',
  ''),
 ('ce6b8c447',
  'sum_basis',
  'not_a_price',
  'lower_bound',
  'цена «Балтики» в несостоявшейся сделке — более 71 млрд рублей, по словам источника',
  'https://www.interfax.ru/russia/929541',
  ''),
 ('g82725e96',
  'title',
  '«Фарминвест» купил «Петровакс» у «Интерроса»',
  'Михаил Цыферов и VB Partners купили «Петровакс» у «Интерроса»',
  '"Интеррос" Владимира Потанина продает свой фармацевтический актив "Петровакс Фарм" менеджменту этой компании '
  'во главе с ее президентом Михаилом Цыферовым и инвесткомпании VB Partners',
  'https://www.interfax.ru/business/865956',
  ''),
 ('g74c84c09',
  'eco.rationale',
  'Покупка добавляет новые бренды к агробизнесу Лисина — агрохолдингу «Румелко».',
  '—',
  '',
  '',
  ''),
 ('g74c84c09',
  'extra',
  'Структуры владельца НЛМК Владимира Лисина в 2024 году купили липецкое АО «Прогресс» — производителя детского '
  'питания «Фрутоняня»; совладелица Ольга Белявцева сохранила долю.',
  'По неофициальным данным, АО «Прогресс» — производителя детского питания «Фрутоняня» — в 2024 году купили '
  'структуры владельца НЛМК Владимира Лисина; совладелица Ольга Белявцева сохранила долю.',
  'Структуры Владимира Лисина приобрели АО «Прогресс» (основные бренды — «Фрутоняня», «Малышам» и «Липецкий '
  'бювет»), сообщил Telegram-канал «M&A Новости» . Информацию подтвердили два источника “Ъ”',
  'https://www.kommersant.ru/doc/7197020',
  ''),
 ('g82725e96',
  'law.struct',
  'По ЕГРЮЛ, 10 октября 2022 года из ООО «НПО Петровакс Фарм» вышел единственный участник — кипрская компания '
  '«Елонда Холдингз Ко. Лимитед», через которую долей владел «Интеррос», и 100% перешли к ООО «Фарминвест». По '
  'данным СПАРК, 75,01% «Фарминвеста» получило ООО «Авеста», которое Цыферов зарегистрировал в августе 2022 года, '
  'остальное — ООО «Прогресс»; «Прогресс» в равных частях принадлежит VB Partners, Михаилу Бройтману, Вагану '
  'Баблояну и Владимиру Евсееву.\n'
  '\n'
  'В октябре 2023 года, по ЕГРЮЛ, «Авеста» стала единственным участником «Фарминвеста», а «Прогресс» из него '
  'вышел.',
  'Покупатели — менеджмент «Петровакса» во главе с президентом компании Михаилом Цыферовым и инвесткомпания VB '
  'Partners; 100% они оформили на ООО «Фарминвест».\n'
  '\n'
  'По ЕГРЮЛ, 10 октября 2022 года из ООО «НПО Петровакс Фарм» вышел единственный участник — кипрская компания '
  '«Елонда Холдингз Ко. Лимитед», через которую долей владел «Интеррос», и 100% перешли к ООО «Фарминвест». По '
  'данным СПАРК, 75,01% «Фарминвеста» получило ООО «Авеста», которое Цыферов зарегистрировал в августе 2022 года, '
  'остальное — ООО «Прогресс»; «Прогресс» в равных частях принадлежит VB Partners, Михаилу Бройтману, Вагану '
  'Баблояну и Владимиру Евсееву.\n'
  '\n'
  'В октябре 2023 года, по ЕГРЮЛ, «Авеста» стала единственным участником «Фарминвеста», а «Прогресс» из него '
  'вышел.',
  '"Интеррос" Владимира Потанина продает свой фармацевтический актив "Петровакс Фарм" менеджменту этой компании '
  'во главе с ее президентом Михаилом Цыферовым и инвесткомпании VB Partners',
  'https://www.interfax.ru/business/865956',
  '')]

GOLD_ROW = ('ce6b8c447',
            {'sum_basis': 'not_a_price',
             'why': '71 млрд ₽ — сумма иска о компенсации, не цена сделки; сделка не состоялась; помечено явным полем sum_basis'},
            {'sum_basis': 'lower_bound',
             'title': 'Carlsberg не смог продать «Балтику» «Арнесту» после указа о временном управлении',
             'why': 'Более 71 млрд ₽ — цена «Балтики» в рамочном соглашении с «Арнестом» (Интерфакс, 08.11.2023: «более 71 млрд '
                    'рублей» с учетом 50%-ного дисконта), нижняя граница; сделка не состоялась — ни в мультипликаторы, ни в '
                    'крупнейшие покупки'})


def gold(write):
    raw = open(GOLD, encoding='utf-8').read()
    g = json.loads(raw)
    row = next(r for r in g['deals'] if r['id'] == GOLD_ROW[0])
    if all(row.get(k) == v for k, v in GOLD_ROW[2].items()):
        return 0
    for k, v in GOLD_ROW[1].items():
        assert row.get(k) == v, ('золотая строка', k, row.get(k))
    row.update(GOLD_ROW[2])
    if write:
        with open(GOLD, 'w', encoding='utf-8') as f:
            f.write(json.dumps(g, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else ''))
    return 1


REMOVE = {}


def _walk(card, path):
    parts = path.split('.')
    obj = card
    for p in parts[:-1]:
        obj = obj[int(p)] if isinstance(obj, list) else obj.setdefault(p, {})
    return obj, (int(parts[-1]) if isinstance(obj, list) else parts[-1])


def _get(card, path):
    obj, k = _walk(card, path)
    if isinstance(obj, list):
        return obj[k]
    return obj.get(k, A)


def merge_step(data):
    import merge_duplicate_deals_batch as mdb
    known_ind = mdb.industries()
    known_themes = {t for d in data['deals'] for t in (d.get('themes') or [])}
    todo, errors = [], []
    for spec in MERGES:
        if (data.get('merged') or {}).get(spec['drop']) == spec['keep']:
            continue
        m = mdb.Merge(data, spec, known_ind, known_themes)
        m.check()
        errors += m.errors
        todo.append(m)
    if errors:
        raise SystemExit('ОТКАЗ слияния: %s' % '; '.join(errors))
    for m in todo:
        m.apply()
    return len(todo)


def apply(data):
    n = merge_step(data)
    by = {d['id']: d for d in data['deals']}
    targets = set((data.get('merged') or {}).values())
    for cid, expect in REMOVE.items():
        if cid not in by:
            continue
        assert expect in str(by[cid].get('title')), (cid, by[cid].get('title'))
        assert cid not in targets, '%s — цель слияния' % cid
        data['deals'] = [d for d in data['deals'] if d['id'] != cid]
        n += 1
    by = {d['id']: d for d in data['deals']}
    for cid, path, old, new, quote, url, flags in OPS:
        c = by[cid]
        cur = _get(c, path)
        if cur == new:
            continue
        assert cur == old, (cid, path, cur)
        obj, k = _walk(c, path)
        if new == A:
            del obj[k]
        else:
            obj[k] = new
        if path in RETRACT and old not in (A, None, '—') and 'noretract' not in flags:
            c.setdefault('retracted', {}).setdefault(path, []).append(old)
        if path in fact_edit_guard.FACT_FIELDS and quote:
            fact_edit_guard.log(c, path, None if new == A else new, quote, url, BY, DAY)
        n += 1
    return n


def cleanup(gone):
    """Снятые и слитые карточки: записи правок, очередь расхождений фактов, признаки будущих сделок."""
    import fix_files
    for cid in gone:
        fix_files.drop_fixes_for(cid, write=True)
    if os.path.exists(DISCREP):
        q = json.load(open(DISCREP, encoding='utf-8'))
        kept = [r for r in q if r.get('id') not in gone]
        if len(kept) != len(q):
            json.dump(kept, open(DISCREP, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    if os.path.exists(SIGNALS):
        raw_s = open(SIGNALS, encoding='utf-8').read()
        sig = json.loads(raw_s)
        keep = [r for r in sig['signals'] if r.get('deal_id') not in gone]
        if len(keep) != len(sig['signals']):
            sig['signals'] = keep
            with open(SIGNALS, 'w', encoding='utf-8') as f:
                f.write(json.dumps(sig, ensure_ascii=False, indent=1) + ('\n' if raw_s.endswith('\n') else ''))


def main(write):
    raw = open(DATA, encoding='utf-8').read()
    old, data = json.loads(raw), json.loads(raw)
    n = apply(data) + gold(False)
    if not n:
        print('Уже применено.')
        return 0
    mass_edit_guard.check(old, data, os.environ.get('MASS_OK'))
    bad = fact_edit_guard.unbacked(old, data)
    assert not bad, bad
    if not write:
        print('Сухой прогон: правок базы %d. Запись — с ключом --write.' % n)
        return 0
    fresh_raw = open(DATA, encoding='utf-8').read()
    fresh = json.loads(fresh_raw)
    apply(fresh)
    with open(DATA, 'w', encoding='utf-8') as f:
        f.write(json.dumps(fresh, ensure_ascii=False, indent=1) + ('\n' if fresh_raw.endswith('\n') else ''))
    gold(True)
    cleanup(list(REMOVE) + [m['drop'] for m in MERGES])
    print('ЗАПИСАНО: правок базы %d.' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv[1:]))
