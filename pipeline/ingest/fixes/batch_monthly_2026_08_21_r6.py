# -*- coding: utf-8 -*-
"""Месячный дообыск 21 августа 2026, шестая партия — последние пять
карточек очереди G7 (X5/«Форвард-Маркет», Atrium/«Парк Хаус»,
Агрокомплекс Ткачева/«Юг Руси», Bonava/Star Development, Полипласт/
«Русский Хром 1915»). Здесь только записи в изначально ПУСТЫЕ/
заглушечные поля — правки уже занятых полей смотри в разовых скриптах
`pipeline/fix_x5_forward_market_followup.py`,
`pipeline/fix_atrium_parkhouse_followup.py`,
`pipeline/fix_yug_rusi_aftermath.py`,
`pipeline/fix_bonava_star_dev_followup.py`,
`pipeline/fix_hrompik_followup.py`.
"""

FIXES = [
    # --- Atrium/«Парк Хаус» (gfa0fe27a) ---
    # gfa0fe27a law.appr: перевод с английского (ALUMNI Partners,
    # англоязычная страница) — дословную проверку review.py не пройдёт
    # ни при каком переводе, правка разовым скриптом
    # pipeline/fix_atrium_parkhouse_followup.py.
    dict(id='gfa0fe27a', field='eco.rationale', old=None,
         new='Компания «Рамо-М» приобрела торговые центры в большей '
             'степени для того, чтобы сохранить жизнеспособность '
             'актива и рабочие места.',
         quote='компания «Рамо-М» приобрела торговые центры «в большей '
               'степени для того, чтобы сохранить жизнеспособность '
               'актива и рабочие места»',
         why='цель сделки со стороны покупателя — Profashion.ru'),
    dict(id='gfa0fe27a', field='src', old=None,
         new=['Denuo', 'https://denuo.legal/en/insights/releases/230511/'],
         quote='Denuo has advised the Romex Group holding on the '
               'acquisition of seven Park House shopping centres',
         why='юридический консультант покупателя и структура сделки'),
    dict(id='gfa0fe27a', field='src', old=None,
         new=['ALUMNI Partners', 'https://alumnipartners.ru/en/'
              'projects/45/'],
         quote='legal assistance with successful application for the '
               'approval of the deal to the Governmental Commission',
         why='подтверждение согласования правкомиссии'),
    dict(id='gfa0fe27a', field='src', old=None,
         new=['Profashion', 'https://profashion.ru/business/finance/'
              'evropeyskiy-investfond-prodal-set-tts-park-khaus/'],
         quote='сохранить жизнеспособность актива и рабочие места',
         why='источник для eco.rationale'),

    # --- Bonava/Star Development (gec6e9db6) ---
    dict(id='gec6e9db6', field='src', old=None,
         new=['ГК ФСК', 'https://fsk.ru/about/news/gk-fsk-stala-'
              'sobstvennikom-rossijskih-aktivov-shvedskogo-'
              'developera-bonava'],
         quote='Посредством сделки с Bonava мы пополняем продуктовую '
               'линейки перспективными проектами бизнес-класса',
         why='официальный пресс-релиз ГК ФСК о закрытии сделки'),
    dict(id='gec6e9db6', field='src', old=None,
         new=['DP.ru', 'https://www.dp.ru/a/2024/04/12/'
              'srazu-tri-developera-v-peterburge'],
         quote='находится в процессе реорганизации',
         why='источник для судьбы БН Девелопмент после сделки'),
    dict(id='gec6e9db6', field='src', old=None,
         new=['DP.ru', 'https://www.dp.ru/a/2024/12/13/'
              'bivshij-proekt-shvedskoj-bonava'],
         quote='ЗПИФ «ФСК Капитал Инвестиции»',
         why='источник для судьбы проекта Magnifika'),

    # --- Агрокомплекс Ткачева/«Юг Руси» (gba72051d) ---
    dict(id='gba72051d', field='src', old=None,
         new=['Интерфакс', 'https://www.interfax.ru/business/1082333'],
         quote='Ключевые предприятия агрохолдинга "Юг Руси" завершили '
               '2025 год с чистым убытком',
         why='финансовые итоги 2025 года'),
    dict(id='gba72051d', field='src', old=None,
         new=['Ведомости', 'https://www.vedomosti.ru/strana/central/'
              'news/2025/12/02/1159925-maslozavoda-chernozeme'],
         quote='маслозаводы в Белгородской области',
         why='продажа трёх заводов в декабре 2025 года'),
    dict(id='gba72051d', field='src', old=None,
         new=['Коммерсантъ', 'https://www.kommersant.ru/doc/6196897'],
         quote='рентабельность маслозаводов остается отличной',
         why='комментарии аналитиков в момент сделки'),
    dict(id='gba72051d', field='src', old=None,
         new=['Блокнот Ростов', 'https://bloknot-rostov.ru/news/'
              'yug-rusi-prodali-tkachevu-levyy-bereg-dona-'
              'zastroya-1688216'],
         quote='после продажи активов покинул Россию',
         why='судьба Сергея Кислова после продажи'),
    dict(id='gba72051d', field='src', old=None,
         new=['161.RU', 'https://161.ru/text/business/2024/12/26/'
              '74926805'],
         quote='передал свои компании в России Василию Васильевичу '
               'Кислову',
         why='передача остававшихся активов Кислова, декабрь 2024'),

    # --- Полипласт/«Русский Хром 1915» (g03ae93e7) ---
    dict(id='g03ae93e7', field='src', old=None,
         new=['Бизнес-журнал Урал', 'https://ural.business-magazine.'
              'online/fn_1688599.html'],
         quote='Более 60 млрд рублей планируется вложить до конца '
               '2026 года',
         why='инвестиционная программа и производственные показатели '
             'после сделки'),
    dict(id='g03ae93e7', field='src', old=None,
         new=['Коммерсантъ', 'https://www.kommersant.ru/doc/6212247'],
         quote='«Хромпик» под новым управлением',
         why='подтверждение переименования в «Хромпик»'),
]
