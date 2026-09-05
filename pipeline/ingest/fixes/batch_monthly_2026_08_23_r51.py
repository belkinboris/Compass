# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), дельта-поиск 23 августа: карточки
gc2a1693a (ВТБ/«Открытие» — 5 сентября 2026 слита в gc3d735fc,
fix_audit_2026_09_05_data.py, её записи отсюда сняты) и gf9932079 (ВЭБ.РФ/«Просвещение») — поля,
заполняемые ОДНИМ источником каждое (комбинированные многоисточниковые
находки — отдельными скриптами, см. fix_vtb_otkritie_post_merger_facts.py
и fix_prosveschenie_2026_governance_change.py). Плюс источники к этим
двум карточкам и к g21c5ee1e (Frankfurt-Hahn, см.
fix_frankfurt_hahn_deal_failed.py).

Запуск: python3 pipeline/ingest/review.py --write
"""

FIXES = [
    dict(
        id='gf9932079', field='law.struct', old='—',
        new='На 31 декабря 2025 года акционерами АО «Просвещение» '
            'являлись: ООО «Перспективные промышленные и инфраструктурные '
            'технологии – 12» - 25% и АО Управляющая компания «Молния» '
            'Д.У. ЗПИФ комбинированный «Образовательная платформа» - 75%. '
            'Конечной контролирующей стороной акционеров является '
            'Российская Федерация.',
        quote='На 31 декабря 2025 года акционерами АО «Просвещение» '
              'являлись: ООО «Перспективные промышленные и '
              'инфраструктурные технологии – 12» - 25% и АО Управляющая '
              'компания «Молния» Д.У. ЗПИФ комбинированный '
              '«Образовательная платформа» - 75%. Конечной контролирующей '
              'стороной акционеров является Российская Федерация.',
        why='формальная структура владения через промежуточные ЗПИФ/УК на конец 2025 года',
    ),
    dict(
        id='gf9932079', field='eco.fin', old='—',
        new='Выручка АО «Просвещение» по РСБУ за 2025 год снизилась на '
            '61,2% до 10,6 млрд руб. с 27,4 млрд руб. годом ранее. Чистая '
            'прибыль упала на 60,5% до 10,79 млрд руб.',
        quote='Выручка АО «Просвещение» по РСБУ за 2025 год снизилась на '
              '61.2% до 10.6 млрд руб. с 27.4 млрд руб. годом ранее. '
              'Чистая прибыль упала на 60.5% до 10.79 млрд руб.',
        why='финансовые результаты головного юрлица группы за 2025 год',
    ),
    dict(id='gf9932079', field='src', old=None,
         new=['Ведомости (13.02.2026)',
              'https://www.vedomosti.ru/media/articles/2026/02/13/1176245-veb-rf-konsolidiruet'],
         quote='к управленческой команде присоединятся представители VK',
         why='ВЭБ.РФ становится единоличным исполнительным органом, VK — стратегическим партнёром'),
    dict(id='gf9932079', field='src', old=None,
         new=['РИА Новости (13.02.2026)', 'https://ria.ru/20260213/protsess-2074301061.html'],
         quote='Совет директоров рекомендовал акционерам принять решение о '
               'передаче полномочий единоличного исполнительного органа',
         why='официальная формулировка о передаче полномочий ВЭБ.РФ'),
    dict(id='gf9932079', field='src', old=None,
         new=['Коммерсантъ (13.02.2026)', 'https://www.kommersant.ru/doc/8438720'],
         quote='Зампред ВЭБ.РФ Александр Тарабрин назначен ответственным за руководство издательством',
         why='назначение куратора от ВЭБ.РФ'),
    dict(id='gf9932079', field='src', old=None,
         new=['AKM.ru', 'https://www.akm.ru/news/prosveshchenie_vyplatilo_dividendy_svoim_aktsioneram/'],
         quote='На 31 декабря 2025 года акционерами АО «Просвещение» являлись',
         why='структура владения и финансовые результаты 2025 года'),
    dict(id='g21c5ee1e', field='src', old=None,
         new=['LTO.de', 'https://www.lto.de/recht/kanzleien-unternehmen/k/'
              'flughafen-hahn-frankfurt-insolvenz-bieter-kauf-neuer-interessent'],
         quote='Der Start eines vollständig neuen Bieterverfahrens vom Insolvenzverwalter hat uns überrascht',
         why='открытие повторного конкурса покупателей конкурсным управляющим'),
    dict(id='g21c5ee1e', field='src', old=None,
         new=['Tagesspiegel', 'https://www.tagesspiegel.de/wirtschaft/'
              'verkaufspoker-findet-ein-ende-trierer-triwo-ag-ubernimmt-insolventen-flughafen-hahn-9611147.html'],
         quote='Die Triwo habe den höchsten Kaufpreis geboten',
         why='победитель повторного конкурса — Triwo AG'),
    dict(id='g21c5ee1e', field='src', old=None,
         new=['Hahn Airport (о компании)', 'https://www.hahn-airport.de/en/company/about-us'],
         quote='Since May 2023, TRIWO AG is the owner of the airport company TRIWO Hahn Airport GmbH',
         why='подтверждение текущего владельца аэропорта'),
]
