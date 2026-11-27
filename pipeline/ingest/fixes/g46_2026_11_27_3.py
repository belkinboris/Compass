# -*- coding: utf-8 -*-
"""Бэклог G46, часть 3 (27 ноября 2026): открытые вопросы вчерашней вычитки, решенные поиском.

- g2224523e (Imperial Brands): покупатели названы по именам — Retail.ru по ЕГРЮЛ: с 27 апреля
  2022 года владельцами обеих российских компаний Imperial стали четыре человека.
- g46b308d6 (Харьяга): день закрытия — 3 августа 2022 года (Oil & Gas Journal).
- gd0af0377 (Oerlikon): дата 1 июня 2022 года — день договора; день закрытия не раскрыт,
  поэтому смысл даты помечен как подписание.
- g9b852635 («Эталон», Нагатинская пойма): продажа впервые объявлена 18 ноября 2026 года
  («Московская перспектива» со ссылкой на телеграм-канал «Стройки — и точка»); 23-е — день,
  когда компания подтвердила РИА Недвижимость.
- g32cfa1d4 (Salmon): $90 млн — обязательства инвесторов профинансировать компанию, а не акции.
- gcc75fe11 (Aptar): убыток группы от потери российской компании — $58 млн (отчет за III квартал).
- c374fc2ca / baltika: условие о казахстанском и азербайджанском бизнесе Carlsberg — условие
  продажи «Балтики» «ВГ Инвест», а не временного управления: перенесено в карточку продажи.

Запуск: python3 pipeline/ingest/review.py  (сухой прогон), запись — родителем партии.
"""

CARDS = ['g2224523e', 'g46b308d6', 'gd0af0377', 'g9b852635', 'g32cfa1d4', 'gcc75fe11',
         'c374fc2ca', 'baltika']

U_IMP = ('https://www.retail.ru/news/proizvoditel-sigaret-imperial-brands-peredal-prava-na-brend-'
         'sigaret-west-novym-s-18-avgusta-2022-219542/')
Q_IMP = ('С 27 апреля новыми владельца стали Александр Кобзев, Константин Иванов, Сергей Бронецкий '
         'и Александр Наумов.')

U_OGJ = ('https://www.ogj.com/general-interest/companies/article/14281846/totalenergies-to-divest-'
         'termokarstovoye-gas-field-interest-to-novatek')
Q_OGJ = ('The company finalized the sale of its remaining 20% interest in Kharyaga to state-controlled '
         'operator Zarubezhneft on Aug. 3, 2022.')

U_OERL = 'https://www.oerlikon.com/ecoma/files/16_Financial_Report_2022_en.pdf'
Q_OERL = ('On June 1, 2022 Oerlikon signed a contract for the sale of all subsidiaries in Russia to the '
          'local management.')

U_ETAL = 'https://mperspektiva.ru/topics/etalon-vystavil-na-prodazhu-zemlyu-v-nagatinskoy-poyme/'
Q_ETAL = ('«Эталон» выставил на продажу землю в Нагатинской пойме 18 ноября 2026 11:12 Девелопер '
          '«Эталон» продает два участка общей площадью 2,2 га в Нагатинской пойме за 8,1 млрд рублей.')

U_SALM = ('https://www.dealstreetasia.com/stories/philippines-fintech-salmon-secures-140m-in-'
          'additional-equity-debt-498489')
Q_SALM = ('has announced raising $140 million in capital through a mix of new commitment and public '
          'bonds. The financing round comprises $90 million in financing commitments from Spice '
          'Expeditions, Washington University Investment Management Company, Moore Strategic Ventures, '
          'and other existing backers. The remainder comprises a $50-million public bond issuance.')
Q_SALM_RU = 'Филиппинский финтех-стартап Salmon бывших управленцев «Тинькофф» привлёк $140 млн'
Q_SALM_SUM = Q_SALM_RU + ' … ' + Q_SALM
W_SALM = ('источники называют $90 млн обязательствами профинансировать компанию (financing commitments), '
          'а не покупкой акций; разбивка по частям — в law.struct')

U_APT = 'https://finviz.com/news/412253/aptar-reports-third-quarter-2026-results'
Q_APT = ('During the third quarter, Aptar deconsolidated its Russian subsidiary following a governmental '
         'decree placing the subsidiary under external administration and the resulting loss of control. '
         'Aptar recorded a $58.0 million loss on deconsolidation which included approximately $30.0 '
         'million of cash held by the subsidiary.')

U_BALT = 'https://www.interfax.ru/business/996240'
Q_BALT_KZ = ('По итогам сделки Carlsberg сохраняет за собой активы в Азербайджане и Казахстане, которые '
             'сейчас принадлежат российскому юрлицу.')
Q_BALT = ('Помимо этого, все судебные споры между сторонами, в том числе связанные с лицензионными '
          'правами, будут урегулированы в рамках сделки … В октябре 2023 года Carlsberg Group расторгла '
          'с "Балтикой" лицензионные соглашения на производство и продажу всей продукции группы, '
          'включая международные и локальные бренды. … ' + Q_BALT_KZ)

FIXES = [
    # ---------------- g2224523e — Imperial Brands
    {'id': 'g2224523e', 'field': 'src', 'old': None, 'new': ['Retail.ru', U_IMP],
     'quote': Q_IMP, 'url': U_IMP, 'why': 'источник, называющий покупателей по ЕГРЮЛ'},
    {'id': 'g2224523e', 'field': 'buyer_name', 'old': 'Местные инвесторы (имена не раскрыты)',
     'new': 'Александр Кобзев, Константин Иванов, Сергей Бронецкий и Александр Наумов',
     'quote': Q_IMP, 'url': U_IMP,
     'why': 'по ЕГРЮЛ с 27 апреля 2022 года обе компании получили четыре человека — они и есть покупатели; '
            '«имена не раскрыты» устарело (docs/card_parties.md: покупатели-люди — по именам)'},
    {'id': 'g2224523e', 'field': 'extra',
     'old': 'Британская Imperial Brands передала российский бизнес с волгоградской фабрикой неназванным '
            'местным инвесторам.',
     'new': 'Британская Imperial Brands передала российский бизнес с волгоградской фабрикой четырем '
            'россиянам: с 27 апреля его совладельцами записаны Александр Кобзев, Константин Иванов, '
            'Сергей Бронецкий и Александр Наумов.',
     'quote': Q_IMP, 'url': U_IMP, 'why': 'покупатели уже названы по реестру'},

    # ---------------- g46b308d6 — Харьягинский проект
    {'id': 'g46b308d6', 'field': 'date', 'old': '2022', 'new': '2022-08-03',
     'quote': Q_OGJ, 'url': U_OGJ,
     'why': 'день завершения продажи назван прямо; в law.struct он уже записан'},
    {'id': 'g46b308d6', 'field': 'date_basis', 'old': None, 'new': 'closing',
     'quote': Q_OGJ, 'url': U_OGJ, 'why': '3 августа 2022 года — завершение продажи'},

    # ---------------- gd0af0377 — Oerlikon
    {'id': 'gd0af0377', 'field': 'date_basis', 'old': None, 'new': 'signing',
     'quote': Q_OERL, 'url': U_OERL,
     'why': 'день закрытия не раскрыт ни пресс-релизом, ни годовым отчетом; 1 июня 2022 года — день договора'},

    # ---------------- g9b852635 — «Эталон», Нагатинская пойма
    {'id': 'g9b852635', 'field': 'date', 'old': '2026-11-23', 'new': '2026-11-18',
     'quote': Q_ETAL, 'url': U_ETAL,
     'why': 'продажу впервые объявили 18 ноября (телеграм-канал «Стройки — и точка», «Московская '
            'перспектива» в тот же день); 23 ноября компания только подтвердила ее РИА Недвижимость — '
            'дата идущей продажи по первому объявлению, а не по перепечатке (docs/card_status_dates.md)'},
    {'id': 'g9b852635', 'field': 'date_basis', 'old': None, 'new': 'announcement',
     'quote': Q_ETAL, 'url': U_ETAL, 'why': 'день первого сообщения о продаже'},

    # ---------------- g32cfa1d4 — Salmon
    {'id': 'g32cfa1d4', 'field': 'sum', 'old': '$140 млн ($90 млн акции, $50 млн облигации)',
     'new': '$140 млн',
     'quote': Q_SALM_SUM, 'url': U_SALM, 'why': W_SALM},
    {'id': 'g32cfa1d4', 'field': 'eco.sum', 'old': '$140 млн ($90 млн акции, $50 млн облигации)',
     'new': '$140 млн',
     'quote': Q_SALM_SUM, 'url': U_SALM, 'why': W_SALM},

    # ---------------- gcc75fe11 — Aptar
    {'id': 'gcc75fe11', 'field': 'src', 'old': None,
     'new': ['AptarGroup (отчет за III квартал 2026 года)', U_APT],
     'quote': Q_APT, 'url': U_APT, 'why': 'отчет продавца о последствиях указа'},
    {'id': 'gcc75fe11', 'field': 'eco.val', 'old': '—',
     'new': 'После указа о временном управлении AptarGroup перестала считать российскую компанию своей '
            'и записала убыток $58,0 млн; в эту сумму вошли около $30,0 млн денег на ее счетах.',
     'quote': Q_APT, 'url': U_APT,
     'why': 'потеря для владельца — как у Fortum (g7fc9f764) в «Оценке»'},

    # ---------------- c374fc2ca / baltika — условие продажи переезжает в карточку продажи
    {'id': 'c374fc2ca', 'field': 'law.terms',
     'old': 'По условиям выхода Carlsberg сохранила 100% в своих казахстанском и азербайджанском бизнесах.',
     'new': '—',
     'quote': Q_BALT_KZ, 'url': U_BALT,
     'why': 'это условие продажи «Балтики» «ВГ Инвест» в декабре 2024 года (своя карточка baltika), '
            'у временного управления условий нет; факт перенесен в law.terms карточки продажи'},
    {'id': 'baltika', 'field': 'src', 'old': None, 'new': ['Интерфакс', U_BALT],
     'quote': Q_BALT_KZ, 'url': U_BALT, 'why': 'источник условия о бизнесе в Казахстане и Азербайджане'},
    {'id': 'baltika', 'field': 'law.terms',
     'old': 'В периметре сделки урегулированы все судебные споры сторон, включая споры о лицензиях на '
            'товарные знаки, расторгнутых Carlsberg в 2023 году.',
     'new': 'В периметре сделки урегулированы все судебные споры сторон, включая споры о лицензиях на '
            'товарные знаки, расторгнутых Carlsberg в 2023 году. Бизнес в Азербайджане и Казахстане, '
            'который принадлежал «Балтике», Carlsberg по условиям сделки оставила себе.',
     'quote': Q_BALT, 'url': U_BALT,
     'why': 'условие перенесено из карточки временного управления (c374fc2ca), где оно стояло не на месте'},
]
