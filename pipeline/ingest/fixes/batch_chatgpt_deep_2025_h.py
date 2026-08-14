# -*- coding: utf-8 -*-
"""Глубокая ревизия 2025 (партия 8), карточки 56–65 из «сотки».

Все 10 карточек — «обыскано под 12 углов, больше ничего не нашлось».

Находки:
  g5880d206 (Volkswagen Bank / Пихта Банк): +src AKM.ru.
  g7edd263c (ERA Capital / Rubetek): +src Sostav.ru.
  g6a6de6a6 (Медси / Bioniq): +src RB.ru.
  ga69530bc (S7 / БЭМЗ): +src Коммерсантъ.
  g7d64b437, g0748e794, gc88ca79d, gf3a811bd,
  g0201b97a, c8b5a234d, g7edd263c, g5880d206: deep_researched.
"""

FIXES = [
    # === g5880d206: Volkswagen Bank RUS → Пихта Банк ===
    # AKM.ru фиксирует смену владельца (Фольксваген → частный покупатель)
    # и переименование банка. Коммерсантъ (разрешение президента) уже в src.
    dict(id='g5880d206', field='src', old=None,
         new=['AKM.ru',
              'https://www.akm.ru/news/folksvagen_bank_rus_smenil_vladeltsa/'],
         quote='Фольксваген Банк РУС сменил владельца',
         why='AKM документирует факт закрытия сделки и смены наименования; '
             'скачан и сверен'),

    # === g7edd263c: ERA Capital / Rubetek ===
    # Sostav.ru подтверждает: ERA Capital приобретает 45% в Rubetek за 1,5 млрд.
    dict(id='g7edd263c', field='src', old=None,
         new=['Sostav.ru', 'https://www.sostav.ru/publication/era-capital-73157.html'],
         quote='ERA Capital инвестирует 1,5 млрд рублей в разработчика IoT-решений Rubetek',
         why='Sostav подтверждает сумму и покупателя; детали структуры '
             '(45% за 1,5 млрд); скачан и сверен'),

    # === g6a6de6a6: Медси / Bioniq (25% → Викторов) ===
    # RB.ru подтверждает факт продажи Медси доли в сервисе Bioniq.
    dict(id='g6a6de6a6', field='src', old=None,
         new=['RB.ru', 'https://rb.ru/news/medsi-medtech-bionic/'],
         quote='«Медси» продала долю в убыточном сервисе Bioniq',
         why='RB.ru — независимый источник, подтверждающий имя покупателя '
             '(Викторов) и факт сделки; скачан и сверен'),

    # === ga69530bc: S7 Group / БЭМЗ ===
    # Коммерсантъ раскрывает суммарные инвестиции S7 в ремонт шасси БЭМЗ.
    dict(id='ga69530bc', field='src', old=None,
         new=['Коммерсантъ', 'https://www.kommersant.ru/doc/8763693'],
         quote='Общие инвестиции группы S7 в предприятие составят 5,8 млрд рублей '
               'с учетом ранее вложенных средств.',
         why='Коммерсантъ раскрывает суммарный объём инвестиций S7 Group в БЭМЗ; '
             'скачан и сверен'),
]
