# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), дельта-поиск 23 августа: новые
источники к g694126dd (ТЦ «Старт») и g8348fea5 («Сибирский Молл») — сами
факты уже дописаны в extra одноразовыми скриптами
(fix_start_bestkon_demolition.py, fix_sibirsky_moll_demolition_plans.py),
здесь только ссылки.

Запуск: python3 pipeline/ingest/review.py --write
"""

FIXES = [
    dict(id='g694126dd', field='src', old=None,
         new=['MSK1.RU', 'https://msk1.ru/text/gorod/2026/02/07/76237165/'],
         quote='На Ленинградском проспекте сносят торговый центр «Старт». '
               'Рабочие уже практически полностью разобрали фасад здания',
         why='снос здания и планы застройки, версия февраля 2026'),
    dict(id='g694126dd', field='src', old=None,
         new=['Москвич Mag',
              'https://moskvichmag.ru/gorod/'
              'delovoj-kompleks-iz-dvuh-neboskrebov-postroyat-na-meste-tts-start-na-leningradskom-prospekte'],
         quote='Общая площадь комплекса — около 210 тыс. кв. м, ввод в '
               'эксплуатацию намечен на 2029 год',
         why='вторая, более ранняя версия проекта застройки (декабрь 2025)'),
    dict(id='g8348fea5', field='src', old=None,
         new=['Коммерсантъ-Сибирь', 'https://www.kommersant.ru/doc/7167855'],
         quote='Владелец торгового центра «Сибирский Молл» девелопер '
               'Александр Бойко заявил, что здание ТРЦ будет снесено',
         why='объявление о планах снести ТРЦ и построить многофункциональный центр'),
    dict(id='g8348fea5', field='src', old=None,
         new=['nsknews.info',
              'https://nsknews.info/materials/'
              'v-novosibirske-snesut-sibirskiy-moll-i-postroyat-715-tysyach-kvadratov/'],
         quote='Думаю, что через три года будем выходить на площадку',
         why='интервью Бойко о сроках проекта и ограничениях по договорам аренды'),
    dict(id='g8348fea5', field='src', old=None,
         new=['Mail/BFM.RU-Новосибирск', 'https://news.mail.ru/economics/62908216/'],
         quote='Александр Бойко категорически опроверг эти сведения, '
               'заявив о искажении его слов в СМИ',
         why='опровержение слухов о сносе, прозвучавшее через несколько дней'),
]
