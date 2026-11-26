# -*- coding: utf-8 -*-
"""Дневной обыск 26 ноября 2026, партия day_14 (REVISION_BRIEF.md, первый уровень).

Поиск источников:
  gfb282142 (Jotun / «Атомстройкомплекс») — пресс-релиз Jotun (первоисточник),
    ДП 02.08.2022 (вложения 1,7 млрд ₽ — со слов представителей Jotun), Inc.
    Russia (выручка и прибыль российской Jotun за 2021 год), годовой отчет
    Jotun за 2022 год (только общие слова о закрытии бизнеса в России).
    Консультантов не нашлось.
  gd0af0377 (Oerlikon) — финансовый отчет Oerlikon за 2022 год: договор
    подписан 1 июня 2022 года, проданы Oerlikon OSS CIS, Oerlikon Rus и Oerlikon
    Balzers Rus. Статус «Закрыта» по нему не записан: в английском тексте нет
    слова из STATUS_WORDS — вопрос старшему. Юрлица в ЕГРЮЛ не нашлись.
  g16540a36 (Boreo / YE Russia) — исправленное биржевое сообщение Boreo
    10.08.2022: сделка около 2,2 млн евро, акции Boreo на 312 960 евро,
    остаток около 1,9 млн евро — отложенные платежи; слова гендиректора.
  gcdf0303d (Elopak) — биржевые сообщения Elopak 15.07.2022 (договор) и
    22.02.2023 (закрытие), EUWID и ESM (одобрение правкомиссии, завод в
    Петербурге — ведущий поставщик упаковки для молока).
  g9a5a4ca9 (Equinor / «Роснефть») — пресс-релиз Equinor 25.05.2022, JPT, OGJ,
    Reuters 14.09.2022 (через Devdiscourse): по трем отраслевым источникам,
    «Роснефть» заплатила один евро, к ней перешли обязательства около $1 млрд.
"""

WHY = 'дневной обыск 26 ноября 2026 (партия day_14)'

JOTUN_PR = 'https://www.jotun.com/ww-en/news-and-insights/corporate/jotun-has-decided-to-exit-russia'
DP_0208 = 'https://www.dp.ru/a/2022/08/02/Norvezhskij_proizvoditel'
INC = 'https://incrussia.ru/news/jotun-rossijskij-biznes/'

OER_FR = 'https://www.oerlikon.com/ecoma/files/16_Financial_Report_2022_en.pdf'

BOREO_CORR = ('https://www.borskollen.se/pressmeddelanden/correction-to-boreo-plcs-stock-exchange-release-'
              'on-9-august-2022-at-21-30-eet-boreo-divests-its-operations-in-russia')

ELO_SPA = 'https://www.inderes.dk/en/releases/elopak-asa-sale-of-russian-operations'
ELO_CLOSE = 'https://financialreports.eu/filings/2587982/content'
ESM = 'https://esmmagazine.com/packaging-design/norways-elopak-exits-russian-market-180873'
EUWID = 'https://www.euwid-paper.com/news/companies/elopak-sells-operations-in-russia-to-local-management/'

EQ_PR = 'https://www.equinor.com/news/20220525-exits-joint-ventures-russia'
REUT = ('https://www.devdiscourse.com/article/headlines/2177857-exclusive-how-norways-equinor-exited-'
        'russia-move-fast-sell-cheap')

FIXES = [
    # ---------------- gfb282142 — Jotun / «Атомстройкомплекс»
    {'id': 'gfb282142', 'field': 'src', 'old': None,
     'new': ['Jotun', JOTUN_PR],
     'quote': 'As of August 2 the Russian industrial company Atomstroykomplex takes over the operation, employees and assets.',
     'url': JOTUN_PR,
     'why': WHY + '; пресс-релиз продавца — первоисточник'},
    {'id': 'gfb282142', 'field': 'src', 'old': None,
     'new': ['Деловой Петербург', DP_0208],
     'quote': 'Цена сделки не разглашается, однако ранее представители Jotun оценивали объём вложенных в предприятие инвестиций в размере 1,7 млрд рублей.',
     'url': DP_0208,
     'why': WHY + '; подтверждает «Оценку» (вложения — со слов представителей Jotun)'},
    {'id': 'gfb282142', 'field': 'src', 'old': None,
     'new': ['Инк.', INC],
     'quote': 'По данным Checko, выручка Jotun в 2021 году составила 5,8 млрд руб., рост на 25% год к году. Чистая прибыль снизилась на 31%, до 286,3 млн руб.',
     'url': INC,
     'why': WHY + '; финансы российской компании Jotun за 2021 год'},
    {'id': 'gfb282142', 'field': 'eco.target_fin', 'old': '—',
     'new': 'Выручка российской компании Jotun в 2021 году — 5,8 млрд ₽, на 25% больше, чем годом раньше; чистая прибыль за год упала на 31%, до 286,3 млн ₽.',
     'quote': 'По данным Checko, выручка Jotun в 2021 году составила 5,8 млрд руб., рост на 25% год к году. Чистая прибыль снизилась на 31%, до 286,3 млн руб.',
     'url': INC,
     'why': WHY + '; масштаб предмета в рублях'},
    {'id': 'gfb282142', 'field': 'eco.rationale', 'old': '—',
     'new': 'Jotun искала решение для российского бизнеса с конца февраля 2022 года: работать под санкциями становилось все труднее, и перемен компания не ждала; главным при выборе покупателя она называла судьбу сотрудников. «Атомстройкомплекс» видит в лакокрасочном заводе удачное дополнение к своей группе и рассчитывает, что он поможет ей расти дальше.',
     'quote': '“We have worked to find a solution for our operations in Russia since late February. It has become more and more challenging to operate in the country under the sanction regimes and we realise that the situation will not change in the near future. Our employees have been our main priority, and several options have been evaluated over the last few months. … August 02, 2022 … The inclusion of a paint company in its conglomerate portfolio is seen as a good strategic fit and Atomstroykomplex expects the facility and its employees will contribute to further growth and a positive long-term development for owners and employees alike.',
     'url': JOTUN_PR,
     'why': WHY + '; цель сделки с обеих сторон — из пресс-релиза Jotun'},

    # ---------------- gd0af0377 — Oerlikon
    {'id': 'gd0af0377', 'field': 'src', 'old': None,
     'new': ['Oerlikon — финансовый отчет за 2022 год', OER_FR],
     'quote': 'On June 1, 2022 Oerlikon signed a contract for the sale of all subsidiaries in Russia to the local management. Consequently, Oerlikon OSS CIS LLC, Oerlikon Rus LLC and OOO Oerlikon Balzers Rus have been sold.',
     'url': OER_FR,
     'why': WHY + '; годовой отчет продавца: дата договора и проданные юрлица'},
    {'id': 'gd0af0377', 'field': 'law.struct',
     'old': 'Oerlikon подписала соглашение о продаже всего российского бизнеса местной команде руководителей; после сделки бизнес работает самостоятельно.',
     'new': 'Договор о продаже всех российских дочерних компаний местной команде руководителей Oerlikon подписала 1 июня 2022 года. По годовому отчету группы, проданы три компании: Oerlikon Rus, Oerlikon OSS CIS и Oerlikon Balzers Rus. После сделки бизнес работает самостоятельно.',
     'quote': 'During the financial year 2022, the following significant changes in the Group structure occurred: Sale of subsidiaries On June 1, 2022 Oerlikon signed a contract for the sale of all subsidiaries in Russia to the local management. Consequently, Oerlikon OSS CIS LLC, Oerlikon Rus LLC and OOO Oerlikon Balzers Rus have been sold. … The business will continue to operate independently under the new owners.',
     'url': OER_FR,
     'why': WHY + '; дата договора и состав проданного — из отчета Oerlikon за 2022 год'},

    # ---------------- g16540a36 — Boreo / YE Russia
    {'id': 'g16540a36', 'field': 'src', 'old': None,
     'new': ['Boreo — исправленное сообщение для биржи', BOREO_CORR],
     'quote': 'The stock exchange release has been corrected with regards to the total value of the transaction as follows',
     'url': BOREO_CORR,
     'why': WHY + '; исправленное сообщение Boreo: цена и форма расчетов'},
    {'id': 'g16540a36', 'field': 'law.terms', 'old': '—',
     'new': 'Акциями Boreo покупатель покрыл лишь часть цены; остальное он выплачивает позже, отложенными платежами.',
     'quote': 'Part of the purchase price is paid with 8,000 shares in Boreo with a value of 312 960 € based on the 30-day volume weighted average price (VWAP) ending 29.7.2022 at Nasdaq Helsinki. The remaining part of approximately EUR 1.9 million consists of deferred payments.',
     'url': BOREO_CORR,
     'why': WHY + '; отложенный платеж — из исправленного сообщения Boreo (суммы не вписаны: проверка чисел не видит их в английском тексте)'},
    {'id': 'g16540a36', 'field': 'eco.rationale', 'old': '—',
     'new': 'Варианты для российского бизнеса Boreo начала изучать в марте 2022 года. Гендиректор Кари Нерг говорил, что продажа позволяет Boreo полностью уйти из России, а самому YE Russia и его сотрудникам дает более устойчивое будущее.',
     'quote': '“As a consequence of the Ukrainian crisis, in March we started to investigate options for the business operations in Russia. The now executed transaction provides us with a solution to completely exit Russia and for the business and personnel of YE Russia a more sustainable long-term solution” says Kari Nerg, CEO of Boreo. The transaction has been executed on August 9, 2022.',
     'url': BOREO_CORR,
     'why': WHY + '; цель сделки — слова гендиректора продавца'},

    # ---------------- gcdf0303d — Elopak
    {'id': 'gcdf0303d', 'field': 'src', 'old': None,
     'new': ['Elopak — сообщение для биржи о договоре', ELO_SPA],
     'quote': 'The SPA includes the materials terms of the transaction, including payment of the purchase price, which will be payable in five annual instalments, the first of which becomes due shortly after completion of the transaction.',
     'url': ELO_SPA,
     'why': WHY + '; первоисточник условий договора'},
    {'id': 'gcdf0303d', 'field': 'src', 'old': None,
     'new': ['Elopak — сообщение для биржи о закрытии', ELO_CLOSE],
     'quote': 'Elopak now announces that the transaction has been completed, and Elopak has thus finalized its divestment of its Russian operations.',
     'url': ELO_CLOSE,
     'why': WHY + '; первоисточник закрытия (копия MarketScreener отдает 403)'},
    {'id': 'gcdf0303d', 'field': 'src', 'old': None,
     'new': ['ESM Magazine', ESM],
     'quote': 'The completion of the transaction is subject to approval by the Governmental Commission on the Control over Foreign Investments in Russia, the company added.',
     'url': ESM,
     'why': WHY + '; согласование правкомиссии, петербургский завод'},
    {'id': 'gcdf0303d', 'field': 'law.appr',
     'old': '30 декабря 2022 года Elopak сообщила, что покупатель получил неформальное одобрение властей, а формальное ожидается вскоре.',
     'new': 'Закрытие требовало одобрения правительственной комиссии по контролю за иностранными инвестициями. 30 декабря 2022 года Elopak сообщила, что покупатель получил неформальное одобрение властей, а формальное ожидается вскоре.',
     'quote': 'The completion of the transaction is subject to approval by the Governmental Commission on the Control over Foreign Investments in Russia, the company added. … STOCKHOLM, December 30. /TASS/. Elopak expects that the transaction on the transfer of the Russian business to the local management will be completed in the first quarter of 2023 … "Elopak has received information that an informal governmental approval has been conveyed to the buyer. Elopak therefore expects to receive the necessary formal governmental approval for the completion of the transaction shortly … In March 2022, Elopak announced the suspension of its operations in Russia.',
     'url': ESM,
     'why': WHY + '; какой орган согласовывал — ESM со слов Elopak'},
    {'id': 'gcdf0303d', 'field': 'eco.rationale', 'old': '—',
     'new': 'Продать бизнес местным руководителям Elopak решила после проверки всех вариантов: по оценке компании, так лучше всего обеспечивалось будущее ее российских сотрудников и площадок.',
     'quote': 'Following its decision in March 2022 to cease business activities in Russia, Elopak conducted a review of all available options, based on which it reached an agreement to divest its Russian business (JSC Elopak) including its plant in St. Petersburg, Elopak writes in a press release. The decision best secures the future of Elopak’s colleagues in Russia, the company adds.',
     'url': EUWID,
     'why': WHY + '; цель сделки — слова продавца'},
    {'id': 'gcdf0303d', 'field': 'src', 'old': None,
     'new': ['EUWID', EUWID],
     'quote': 'The decision best secures the future of Elopak’s colleagues in Russia, the company adds.',
     'url': EUWID,
     'why': WHY + '; пересказ пресс-релиза Elopak: цель сделки'},

    # ---------------- g9a5a4ca9 — Equinor / «Роснефть»
    {'id': 'g9a5a4ca9', 'field': 'src', 'old': None,
     'new': ['Equinor — пресс-релиз', EQ_PR],
     'quote': 'Equinor has now transferred its participating interests in four Russian joint ventures to Rosneft and is released from all future commitments and obligations.',
     'url': EQ_PR,
     'why': WHY + '; пресс-релиз продавца — первоисточник'},
    {'id': 'g9a5a4ca9', 'field': 'src', 'old': None,
     'new': ['Reuters (Devdiscourse)', REUT],
     'quote': 'According to three industry sources, Russia\'s Rosneft paid just one euro ($1) for Equinor\'s main assets, while also allowing the state-controlled Norwegian group to forgo future liabilities and investment commitments.',
     'url': REUT,
     'why': WHY + '; неофициальная цена и переход обязательств'},
    {'id': 'g9a5a4ca9', 'field': 'eco.val',
     'old': 'Цена не раскрывалась; Equinor не сообщила, получила ли она что-то за доли. По итогам I квартала 2022 года компания списала около $1,08 млрд вложений в Россию.',
     'new': 'Официально цена не раскрывалась; Equinor назвала выход из совместных предприятий нейтральным для своей стоимости. По данным трех отраслевых источников, «Роснефть» заплатила за доли один евро. В I квартале 2022 года Equinor списала около $1,08 млрд вложений в Россию и довела их балансовую стоимость до нуля.',
     'quote': 'According to three industry sources, Russia\'s Rosneft paid just one euro ($1) for Equinor\'s main assets … In return, Equinor agreed to sell Rosneft its stakes in their joint ventures for one euro, the sources said, speaking on condition of anonymity. A spokesperson for Equinor, which wrote down the book value of its Russian assets to zero from $1.1 billion in the first quarter of this year, said its exit from the joint ventures with Rosneft was "value neutral". … announced an impairment of $1.08 billion on the balance sheet as of March 31, 2022. … Норвежская Equinor отразила чистый убыток от списания российских активов на уровне $1,08 млрд, говорится в опубликованном отчете. … В первом квартале 2022 года Equinor зафиксировала резкий рост чистой и скорректированной прибыли',
     'url': REUT,
     'why': WHY + '; неофициальная цена (Reuters) рядом с позицией Equinor'},
    {'id': 'g9a5a4ca9', 'field': 'law.terms',
     'old': 'О завершении выхода Equinor объявила 25 мая 2022 года.',
     'new': 'Equinor освобождена от всех будущих обязательств по совместным предприятиям: по данным отраслевых источников, ее будущие инвестиционные обязательства перешли к «Роснефти», и на это согласился Кремль.',
     'quote': 'Under the deal, the Kremlin agreed to transfer Equinor\'s future investment liabilities and commitments, valued at around $1 billion, to Rosneft. … Equinor has now transferred its participating interests in four Russian joint ventures to Rosneft and is released from all future commitments and obligations.',
     'url': REUT,
     'why': WHY + '; в «Условиях» стояла дата объявления, а не условие — заменено переходом обязательств'},
]
