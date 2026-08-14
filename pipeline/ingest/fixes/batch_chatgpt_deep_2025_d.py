# -*- coding: utf-8 -*-
"""Глубокая ревизия 2025 (партия 4), карточки 16–25 из «сотки».

Все 10 карточек — «обыскано под 12 углов, больше ничего не нашлось».

Находки:
  g8ed07ff5 (Западная Голд/ОКТО): buyer_name, +2 src (Zolteh, Level Legal).
  gf9932079 (Просвещение/ВЭБ): +src Interfax.
  g91ec3558 (Азбука вкуса/Магнит): +src New-Retail.
  g2a3a597b (Балтийский берег pre-IPO): +src Коммерсантъ.
  gafc80ee1 (Кропоткинский элеватор/РЗК): +src AKM.ru.
  g09242ae2, g65deaa28, g381ff192, g5d835058, gda5d56f5: только deep_researched.
"""

FIXES = [
    # === g8ed07ff5: ГК «Западная» / Группа «ОКТО» ===
    # Zolteh (отраслевой портал) подтверждает ОКТО как покупателя.
    # Level Legal опубликовала пресс-релиз о своей роли как buyer-side советника.
    dict(id='g8ed07ff5', field='buyer_name', old=None, new='Группа «ОКТО»',
         quote='100% акций МКАО «Западная Голд Майнинг Лимитед» приобрела группа «ОКТО»',
         why='покупатель без профиля — имя и закрытие подтверждены Zolteh.ru'),

    dict(id='g8ed07ff5', field='src', old=None,
         new=['Zolteh.ru',
              'https://zolteh.ru/news/gruppa_okto_priobrela_100_aktsiy_zolotodobyvayushchey_gk_zapadnaya/'],
         quote='100% акций МКАО «Западная Голд Майнинг Лимитед» приобрела группа «ОКТО»',
         why='портал «Золото и технологии» — профильный для горнодобывающей отрасли; '
             'скачан и сверен'),

    dict(id='g8ed07ff5', field='src', old=None,
         new=['Level Legal Services',
              'https://www.level-legal.com/news/yuridicheskaya-firma-level-legal-services-'
              'osushestvila-kompleksnoe-yuridicheskoe-konsultirovanie-chastnogo-investora-v-'
              'svyazi-s-priobreteniem-gk-zapadnaya'],
         quote='Юридическая фирма LEVEL Legal Services осуществила комплексное юридическое '
               'консультирование частного инвестора в связи с приобретением ГК «Западная»',
         why='пресс-релиз советника со стороны покупателя; подтверждает роль и закрытие; '
             'скачан и сверен'),

    # === gf9932079: Просвещение / ВЭБ ===
    # Interfax подтверждает долю ВЭБа (75%) после выкупа доли Сбербанка.
    dict(id='gf9932079', field='src', old=None,
         new=['Interfax', 'https://www.interfax.ru/business/1045712'],
         quote='ВЭБ увеличил долю в издательстве «Просвещение» до 75%. '
               'У ВЭБа — 75%, у РФПИ — 25%.',
         why='Interfax фиксирует результирующие доли после закрытия сделки со Сбером; '
             'скачан и сверен'),

    # === g91ec3558: Азбука вкуса / Магнит ===
    # New-Retail подтверждает итоговую сумму 29,65 млрд руб. (РБК и Ъ уже есть).
    dict(id='g91ec3558', field='src', old=None,
         new=['New Retail',
              'https://new-retail.ru/novosti/retail/magnit_raskryl_summu_pokupki_azbuki_vkusa/'],
         quote='Сумма сделки по приобретению «Азбуки вкуса» составила 29,65 млрд руб.',
         why='отраслевое ретейл-издание со ссылкой на официальное раскрытие Магнита; '
             'скачан и сверен'),

    # === g2a3a597b: Балтийский берег (pre-IPO) ===
    # Коммерсантъ — расширенная статья о параметрах раунда (объём, цель, акционер).
    dict(id='g2a3a597b', field='src', old=None,
         new=['Коммерсантъ', 'https://www.kommersant.ru/doc/7532986'],
         quote='Объем привлеченных средств составит до 4,5 млрд рублей, '
               'которые будут направлены на создание нового производства.',
         why='Коммерсантъ раскрывает параметры pre-IPO: объём, назначение, '
             'долю (до 15%); скачан и сверен'),

    # === gafc80ee1: Кропоткинский элеватор / РЗК «Ресурс» ===
    # AKM.ru фиксирует одобрение ФАС и детали сделки.
    dict(id='gafc80ee1', field='src', old=None,
         new=['AKM.ru',
              'https://www.akm.ru/news/rzk_resurs_poluchil_odobrenie_fas_na_priobretenie_v_'
              'polzovanie_imushchestva_kropotkinskogo_elevatora/'],
         quote='РЗК «Ресурс» получил одобрение ФАС на приобретение в пользование имущества '
               'Кропоткинского элеватора',
         why='информагентство AKM фиксирует одобрение ФАС как дополнительную точку подтверждения; '
             'скачан и сверен'),
]
