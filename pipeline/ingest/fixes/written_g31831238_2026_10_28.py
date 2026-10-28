# -*- coding: utf-8 -*-
"""Текст карточки g31831238, написанный по фактам (write_card.py, WRITING_BRIEF.md).

Сведено из шести промежуточных партий одной сессии (несколько раундов второго
чтения в тот же день переписывали те же поля) в одну запись на поле —
`test_no_duplicate_fix_for_one_field` требует ровно одну запись на (id, field).

Запуск: python3 pipeline/ingest/review.py --write
"""

FIXES = [{'id': 'g31831238',
  'field': 'eco.share',
  'old': '—',
  'new': 'Три основателя Classiq получат от $80 до $100 млн каждый. Отдельно сотрудники компании в '
         'целом совместно владеют около 10% акций — это примерно $230 млн по оценке сделки, и '
         'Intel дополнительно выделила им больше $100 млн грантов на удержание персонала.',
  'quote': 'According to Calcalist, employees collectively own approximately 10% of Classiq, '
           'representing around $230 million at the transaction valuation. Intel has reportedly '
           "allocated more than $100 million in additional retention grants. The company's three "
           'founders are each expected to receive between $80 million and $100 million. … around '
           '$230 … more than $100 … between $80',
  'why': 'текст написан по фактам (WRITING_BRIEF.md); сведено из шести промежуточных партий одной '
         'сессии в одну запись на поле (test_no_duplicate_fix_for_one_field)'},
 {'id': 'g31831238',
  'field': 'eco.val',
  'old': '—',
  'new': 'В мае 2025 года Classiq закрыла раунд серии C под руководством Entrée Capital — размер '
         'раунда и оценку компании по его итогам источники называют по-разному: $135 млн при '
         'оценке $600-700 млн по одним данным, $110 млн при оценке свыше $400 млн (и выручке около '
         '$8-9 млн в год) по другим. Позже в капитал вошли AMD Ventures, Qualcomm Ventures и IonQ. '
         'Цена Intel больше чем втрое выше оценки в $600-700 млн.',
  'quote': 'Its most recent major funding round, in 2025, valued the company at approximately $600 '
           "million to $700 million, making Intel's purchase price more than three times that "
           'valuation. … Classiq has raised over $200 million to date, with its most recent '
           'funding round (a Series C) totaling $135 million at a valuation of $600 million. … '
           'approximately $600 … to $700 … totaling $135 … По данным отраслевых источников, оценка '
           'компании превышает $400 млн при годовой выручке около $8−9 млн. Цена сделки с Intel '
           'заметно выше этого показателя. … В мае 2025 года Classiq закрыла раунд серии C на $110 '
           'млн под руководством Entrée Capital. Позже в капитал вошли AMD Ventures, Qualcomm '
           'Ventures и IonQ, и общая сумма инвестиций превысила $200 млн.',
  'why': 'текст написан по фактам (WRITING_BRIEF.md); сведено из шести промежуточных партий одной '
         'сессии в одну запись на поле (test_no_duplicate_fix_for_one_field)'},
 {'id': 'g31831238',
  'field': 'eco.target_fin',
  'old': '—',
  'new': 'В Classiq по одним данным работает около 130 человек, по другим — около 150. Компания '
         'привлекла больше $200 млн инвестиций. Среди клиентов — BMW и AT&T.',
  'quote': 'The company is small. Bloomberg puts its headcount at about 130, says it has raised '
           'more than $200 million, and names BMW and AT&T among its customers. … Classiq '
           'currently employs approximately 150 … Позже в капитал вошли AMD Ventures, Qualcomm '
           'Ventures и IonQ, и общая сумма инвестиций превысила $200 млн. … The company is small. '
           'Bloomberg puts its headcount at about 130, says it has raised more than $200 million, '
           'and names BMW and AT&T among its customers.',
  'why': 'текст написан по фактам (WRITING_BRIEF.md); сведено из шести промежуточных партий одной '
         'сессии в одну запись на поле (test_no_duplicate_fix_for_one_field)'},
 {'id': 'g31831238',
  'field': 'eco.rationale',
  'old': '—',
  'new': 'Intel хочет стать поставщиком квантовых решений полного цикла — от кремния до программ: '
         'компания соединяет собственное кремниевое спин-кубитное оборудование, которое '
         'разрабатывает с 2015 года, с платформой синтеза Classiq, чтобы добавить к линейке CPU, '
         'GPU и ASIC квантовые процессоры. Технический директор Intel Пушкар Ранаде, ключевой '
         'советник главы компании, представил сделку инвесторам и аналитикам и сравнил роль '
         'Classiq с ролью Cadence, CUDA и DOS в классических вычислениях. Гендиректор Intel Лип-Бу '
         'Тан оценивает потенциал отрасли примерно в десять раз выше масштаба искусственного '
         'интеллекта на классических вычислениях; у Intel сейчас около 70 сотрудников в квантовом '
         'направлении.',
  'quote': "The proposed acquisition of Classiq would combine Intel's quantum software platform, "
           'scalable silicon spin-qubit technology and advanced semiconductor manufacturing '
           "expertise with Classiq's automated quantum algorithm synthesis platform. … Intel has "
           'been working on quantum since 2015, and it took a different road from IBM and Google. '
           "… Intel's CTO Pushkar Ranade, a key adviser to CEO Lip-Bu Tan, presented the deal to "
           'investors and analysts on Tuesday. He described Classiq as playing a role in quantum '
           'computing similar to that of foundational software platforms in conventional '
           "computing, comparing it to CUDA, Nvidia's software platform, and DOS, Microsoft's "
           'early operating system. … В подкасте QuantumJane Тан сравнил Classiq с Cadence: по его '
           'словам, компания хочет занять в квантовых вычислениях место, которое Cadence занимает '
           'в проектировании классических чипов. … По словам Тана, над направлением работают около '
           '70 сотрудников, у Intel есть собственное производство. … Потенциал отрасли Тан оценил '
           'примерно в десять раз выше масштаба ИИ на классических вычислениях.',
  'why': 'текст написан по фактам (WRITING_BRIEF.md); сведено из шести промежуточных партий одной '
         'сессии в одну запись на поле (test_no_duplicate_fix_for_one_field)'},
 {'id': 'g31831238',
  'field': 'eco.context',
  'old': '—',
  'new': 'Гендиректор Intel Лип-Бу Тан — личный инвестор Classiq: он вложился в раунд на $33 млн в '
         '2022 году вместе с венчурными подразделениями HPE и Samsung еще до того как возглавил '
         'Intel, и, по неофициальным данным, не участвовал в переговорах по сделке из-за личного '
         'финансового интереса. Среди институциональных инвесторов Classiq — Entrée Capital, Team8 '
         'Capital и израильский страховщик Phoenix. Тан возглавил Intel в марте 2025 года; до '
         'этого руководил разработчиком программ для проектирования микросхем Cadence Design '
         'Systems, председательствует в Walden International и давно инвестирует в PsiQuantum, в '
         '2026 году войдя в совет директоров этой компании. До сделки с Intel Classiq '
         'рассматривала выход на биржу через SPAC или обычное IPO и была близка к этому, но, по '
         'словам сооснователя и гендиректора компании Нира Минерби, отказалась от этого плана, '
         'потому что рынок публичных квантовых компаний оказался слишком волатильным.',
  'quote': 'Among the major investors are Entrée Capital, Team8 Capital and Israeli insurer '
           'Phoenix. Intel CEO Lip-Bu Tan is also a personal investor in Classiq, having acquired '
           "his stake before becoming Intel's chief executive. According to sources close to the "
           'Israeli company, Tan did not participate in the acquisition negotiations because of '
           "his financial interest. … Tan's own ties run through the quantum field. Before Intel, "
           'he ran Cadence Design Systems and chairs Walden International. He is also a long-time '
           "investor in PsiQuantum and joined that company's board in 2026. … Заметную роль в "
           'сделке сыграл новый генеральный директор Intel Лип-Бу Тан, который возглавил компанию '
           'в марте 2025 года. … Тан входит в число инвесторов Classiq: его личные средства были в '
           'раунде 2022 года на $33 млн, где участвовали также инвестиционные подразделения HPE и '
           'Samsung. … We explored several alternatives recently, including the public markets '
           'through both a SPAC and a traditional IPO.',
  'why': 'текст написан по фактам (WRITING_BRIEF.md); сведено из шести промежуточных партий одной '
         'сессии в одну запись на поле (test_no_duplicate_fix_for_one_field)'},
 {'id': 'g31831238',
  'field': 'law.struct',
  'old': '—',
  'new': 'Сделка оплачивается деньгами и акциями Intel; точное соотношение стороны не раскрыли. До '
         'завершения Intel и Classiq продолжат работать как отдельные независимые компании.',
  'quote': 'On Monday, Intel announced that it would acquire Classiq for $2.3 billion in cash and '
           'stock, following a prolonged period of internal turmoil that had effectively brought '
           'its acquisition activity to a halt. … The transaction is subject to regulatory '
           'approvals and other customary closing conditions and is expected to close in the first '
           'half of 2027.',
  'why': 'текст написан по фактам (WRITING_BRIEF.md); сведено из шести промежуточных партий одной '
         'сессии в одну запись на поле (test_no_duplicate_fix_for_one_field)'},
 {'id': 'g31831238',
  'field': 'law.appr',
  'old': '—',
  'new': 'Закрытие сделки зависит от разрешений регуляторов и ожидается не раньше первой половины '
         '2027 года.',
  'quote': 'The transaction is subject to regulatory approvals and other customary closing '
           'conditions and is expected to close in the first half of 2027.',
  'why': 'текст написан по фактам (WRITING_BRIEF.md); сведено из шести промежуточных партий одной '
         'сессии в одну запись на поле (test_no_duplicate_fix_for_one_field)'},
 {'id': 'g31831238',
  'field': 'law.terms',
  'old': '—',
  'new': 'После закрытия сделки Intel обещает сохранить совместимость программ Classiq с '
         'оборудованием других производителей квантовых компьютеров и продолжит поддерживать уже '
         'существующие интеграции Classiq.',
  'quote': "Following the close of the transaction, Intel intends to continue to support Classiq's "
           'existing multi-platform integrations and ensure a modality- and hardware-agnostic '
           'software solution that continues to enable an open and collaborative quantum software '
           'ecosystem.',
  'why': 'текст написан по фактам (WRITING_BRIEF.md); сведено из шести промежуточных партий одной '
         'сессии в одну запись на поле (test_no_duplicate_fix_for_one_field)'},
 {'id': 'g31831238',
  'field': 'extra',
  'old': '—',
  'new': 'Для Intel покупка Classiq — ставка на квантовые вычисления на фоне продажи других '
         'направлений: в апреле 2025 года компания продала 51% Altera фирме Silver Lake за $4,46 '
         'млрд и рассматривает продажу подразделения сетей и edge с выручкой $5,8 млрд за 2024 '
         'год. Рынок квантовых вычислений консолидируется: в июле 2026 года IBM договорилась о '
         'покупке HRL Laboratories.',
  'quote': 'In April 2025, for example, Intel agreed to sell a 51% stake in its programmable-chip '
           'business, Altera, to private equity firm Silver Lake for $4.46 billion. … Intel has '
           'also considered selling its network and edge unit, once known as NEX, which brought in '
           '$5.8 billion in revenue in 2024. … IBM signed an agreement in July 2026 to buy HRL '
           'Laboratories, the Boeing and General Motors research institution, to add silicon-spin '
           'qubit expertise to its superconducting program. … Silver Lake for $4.46 … brought in '
           '$5.8 … in July 2026',
  'why': 'текст написан по фактам (WRITING_BRIEF.md); сведено из шести промежуточных партий одной '
         'сессии в одну запись на поле (test_no_duplicate_fix_for_one_field)'}]
