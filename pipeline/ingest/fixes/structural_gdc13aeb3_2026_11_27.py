# -*- coding: utf-8 -*-
"""gdc13aeb3 — возможная покупка Imperial Brands (Altria, по неофициальным данным — с Japan Tobacco).

Карточка заведена по решению владельца «это сделка» (сырье d39558738), 27 ноября 2026.
Стороны, предмет, дата и консультанты — по заявлениям Altria и Imperial Brands от 26 ноября
2026 года (правило 2.4 британского Кодекса о поглощениях, полные тексты RNS на 6ix.com) и по
привязанной статье АБН. Консультанты (law.adv) — разовым скриптом
pipeline/fix_gdc13aeb3_advisers_2026_11_27.py: список строк таблицей FIXES не пишется. Участие Japan Tobacco компаниями не подтверждено (Bloomberg, Reuters).
"""

ID = 'gdc13aeb3'
U_ALTRIA = 'https://6ix.com/news/statement-re-possible-offer-94'
U_IMB = 'https://6ix.com/news/statement-re-possible-offer-95'
U_ABN = ('https://abn.agency/2026/11/27/japan-tobacco-rassmatrivayut-pokupku-imperial-brands-na-fone-'
         'vremennogo-upravleniya-aktivami-v-rossii/')
U_REUTERS = 'https://wtaq.com/2026/11/27/japan-tobacco-shares-surge-on-talk-it-may-acquire-part-of-imperial/'
U_RBC = 'https://www.rbc.ru/business/27/11/2026/6b0933c5ec77465cc3999293'
U_VED = 'https://www.vedomosti.ru/investments/news/2026/11/27/1415867-aktsii-japan-tobacco'
U_KOM = 'https://www.kommersant.ru/doc/9142714'

Q_ALTRIA = ('Altria Group, Inc. (“Altria”) notes the recent press speculation and confirms that it is '
            'considering a possible offer for Imperial Brands.')
Q_ABN_JT = ('По данным Bloomberg News, партнером может стать JT: компания изучает возможность приобретения '
            'вместе с другим участником.')
Q_ABN_LEAD = ('Японская Japan Tobacco (JT) и американская Altria планируют приобрести британского '
              'производителя сигарет Imperial Brands и разделить его активы между собой.')
Q_DATE = ('For immediate release 26 November 2026 Possible offer for Imperial Brands PLC (“Imperial Brands”) '
          'Altria Group, Inc. (“Altria”) notes the recent press speculation and confirms that it is '
          'considering a possible offer for Imperial Brands.')

FIXES = [
    {'id': ID, 'field': 'title',
     # История: заголовок новости АБН -> «Altria и Japan Tobacco могут купить Imperial Brands» (сборка) ->
     # нынешний (второе чтение: JT — участник только по неофициальным данным, покупатель в карточке один).
     'old': 'Altria и Japan Tobacco могут купить Imperial Brands',
     'new': 'Altria может купить Imperial Brands — возможно, вместе с Japan Tobacco',
     'quote': Q_ABN_LEAD, 'url': U_ABN,
     'why': 'стандарт заголовка для «Обсуждается» по неофициальным данным — «X может купить Y»; Altria '
            'подтвердила, что рассматривает предложение, участие JT — по данным Bloomberg'},
    {'id': ID, 'field': 'buyer_name', 'old': None, 'new': 'Altria',
     'quote': Q_ALTRIA, 'url': U_ALTRIA,
     'why': 'о возможном предложении объявила только Altria; Japan Tobacco — возможный партнер по данным '
            'Bloomberg, компаниями не подтвержден (об этом — в тексте карточки и в заголовке)'},
    {'id': ID, 'field': 'asset', 'old': None, 'new': 'Imperial Brands',
     'quote': Q_ALTRIA, 'url': U_ALTRIA, 'why': 'возможное предложение — на всю компанию Imperial Brands PLC'},
    {'id': ID, 'field': 'date', 'old': '2026-11-27', 'new': '2026-11-26',
     'quote': Q_DATE, 'url': U_ALTRIA,
     'why': 'о возможном предложении Altria объявила 26 ноября; 27-е — день пересказа АБН'},
    {'id': ID, 'field': 'date_basis', 'old': None, 'new': 'announcement',
     'quote': Q_DATE, 'url': U_ALTRIA, 'why': 'день первого официального сообщения'},
    {'id': ID, 'field': 'src', 'old': None,
     'new': ['Altria, заявление о возможном предложении (26.11.2026)', U_ALTRIA],
     'quote': Q_ALTRIA, 'why': 'первоисточник: заявление Altria по правилу 2.4'},
    {'id': ID, 'field': 'src', 'old': None,
     'new': ['Imperial Brands, ответ на заявление Altria (26.11.2026)', U_IMB],
     'quote': 'The Board has not had any discussions with, or received any approach or proposal from, Altria '
              'or the third party referenced in the Announcement.',
     'why': 'первоисточник: позиция совета директоров Imperial Brands'},
    {'id': ID, 'field': 'src', 'old': None, 'new': ['Reuters', U_REUTERS],
     'quote': 'Imperial, whose shares shot 13.3% higher on Thursday to give it a market value of £25.90 billion '
              '($34 billion), said it has not received any approach, but would consider any proposal.',
     'why': 'Reuters о возможном участии JT и оценке рынка'},
    {'id': ID, 'field': 'src', 'old': None, 'new': ['РБК', U_RBC],
     'quote': 'могло бы частично компенсировать потерю российского бизнеса, над которым японская компания '
              'утратила в ноябре контроль из-за введения временного управления, пишет Reuters .',
     'why': 'российская сторона: потеря контроля JT над российским бизнесом'},
    {'id': ID, 'field': 'src', 'old': None, 'new': ['Ведомости', U_VED],
     'quote': 'Japan Tobacco отказалась комментировать информацию о потенциальной сделке. В Imperial Brands '
              'заявили, что пока не получали предложений о покупке.',
     'why': 'позиции JT и Imperial Brands'},
    {'id': ID, 'field': 'src', 'old': None, 'new': ['Коммерсантъ', U_KOM],
     'quote': 'Американская табачная корпорация Altria рассматривает возможность покупки британского '
              'конкурента Imperial Brands.',
     'why': 'новость из сомнительного сырья d58416413 — та же сделка'},
]
