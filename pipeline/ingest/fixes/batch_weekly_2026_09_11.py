# -*- coding: utf-8 -*-
"""Недельная очередь качества (REVISION_BRIEF, второй уровень — узкая
дельта), 11 сентября 2026: две карточки из шести в очереди получили
новые факты, четыре прочитаны без находок (Минфин/«Леста» — окно
продажи ещё не истекло; Киркоров/«Королевство сладостей»,
«Дом.РФ»/Петергоф торги 18 сентября, «Azimut отель Ярославль» — без
новых публикаций после дочитывания).

Запись обоих полей уже сделана одноразовыми скриптами (с собственным
`assert` на исходное состояние) — здесь только журнал. Правки в поля,
уже занятые старыми записями FIXES (`law.struct` у g70c0a9ff,
`eco.context` у ge0cc0dfe), слиты в УЖЕ существующие записи
(`batch_2026_09_03_nmg_kp_de_facto_2016.py`,
`batch_2026_09_04_severstal_ulugkhemugol_promresurs.py` — там же и их
история), а не заведены вторыми записями — таблица не умеет цепочку
из двух правок на одно поле.
  g70c0a9ff (НМГ/«Комсомольская правда») —
    pipeline/fix_nmg_kp_ldv_press_structure.py
  ge0cc0dfe («Северсталь»/«Улугхемуголь») —
    pipeline/fix_severstal_tuva_promresurs_buyer_bio.py
"""

FIXES = [
    dict(id='g70c0a9ff', field='seller', old=None, new='Сергей Руднов',
         quote='С 2016 года эту долю контролировал Сергей Руднов – сын '
               'основателя «Балтийской медиагруппы» Олега Руднова.',
         why='продавец не был назван вовсе; найден дельта-поиском.'),
    dict(id='g70c0a9ff', field='src', old=None,
         new=['Verstka.media',
              'https://verstka.media/prodavczom-komsomolskoi-pravdy-mediaholdingu-aliny-kabaevoi-okazalsya-nominal-vladimira-putina'],
         quote='9 сентября мультимедийный информационный центр (МИЦ) '
               '«Известия», входящий в НМГ, получил под свой контроль '
               '75,1% компании «ЛДВ Пресс».',
         why='источник структуры сделки и продавца.'),

    dict(id='ge0cc0dfe', field='src', old=None,
         new=['mergers.ru',
              'https://mergers.ru/news/Novosibirskaya-kompaniya-Promresurs-priobrela-ugolnye-aktivy-v-Tuve-87495'],
         quote='Ранее он управлял угольными шахтами в Киселевске и '
               'Прокопьевске Кемеровской области.',
         why='источник биографии и финансов покупателя.'),
]
