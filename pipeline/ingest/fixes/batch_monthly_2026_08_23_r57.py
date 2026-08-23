# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), дельта-поиск 23 августа: карточка
g75920ee3 (IHC/ЛУКОЙЛ) — статус разрешения OFAC (поле было пустой
заглушкой). Плюс источники к этой карточке и к g74fd5cdb (Лента/О'кей,
см. fix_okey_lenta_rebrand_and_control.py и
fix_okey_lenta_deal_structure_precision.py).

Запуск: python3 pipeline/ingest/review.py --write
"""

FIXES = [
    dict(
        id='g75920ee3', field='law.appr', old='Публично не сообщалось',
        new='Минфин США продлил до 19 сентября лицензию, которая '
            'позволяет вести переговоры о продаже, отчуждении или '
            'передаче Lukoil International GmbH.',
        quote='Минфин США продлил до 19 сентября лицензию, которая '
              'позволяет вести переговоры о продаже, отчуждении или '
              'передаче Lukoil International GmbH.',
        why='статус лицензии OFAC на переговоры о продаже (продлена в очередной раз)',
    ),
    dict(id='g75920ee3', field='src', old=None,
         new=['ЛУКОЙЛ (пресс-релиз, 29.01.2026)',
              'http://lukoil.ru/PressCenter/Pressreleases/Pressrelease/lukoil-zakliuchil-soglashenie-s-carlyle-o-prodazhe'],
         quote='ЛУКОЙЛ ЗАКЛЮЧИЛ СОГЛАШЕНИЕ С CARLYLE О ПРОДАЖЕ ЗАРУБЕЖНЫХ АКТИВОВ',
         why='соглашение с Carlyle о продаже LUKOIL International GmbH'),
    dict(id='g75920ee3', field='src', old=None,
         new=['Egypt Oil & Gas (01.02.2026)',
              'https://egyptoil-gas.com/news/carlyle-explores-uae-partnerships-for-20b-acquisition-of-lukoils-global-assets/'],
         quote='Sources indicate a specific interest among UAE investors in Litasco',
         why='изменившаяся роль IHC — миноритарный интерес к Litasco'),
    dict(id='g75920ee3', field='src', old=None,
         new=['ts2.tech (31.01.2026)',
              'https://ts2.tech/en/ihc-stock-price-sits-near-52-week-low-as-carlyle-lukoil-talks-put-abu-dhabis-international-holding-in-play/'],
         quote='the Lukoil deal might not end up materializing for IHC',
         why='оговорка о необязывающем характере переговоров'),
    dict(id='g75920ee3', field='src', old=None,
         new=['Коммерсантъ (21.08.2026)', 'https://www.kommersant.ru/doc/8894083'],
         quote='Минфин США продлил до 19 сентября лицензию',
         why='актуальный статус лицензии OFAC на август 2026'),
    dict(id='g74fd5cdb', field='src', old=None,
         new=['Retail.ru (10.08.2026)', 'https://www.retail.ru/news/'
              'set-lenta-zavershila-sdelku-po-priobreteniyu-gipermarketov-o-key--10-avgusta-2026-280880/'],
         quote='ООО «РБФ Ритейл», подконтрольное «Ленте», 10 августа 2026 года получило 99,56% в УК «О’кей»',
         why='прямое владение «Ленты» через РБФ Ритейл'),
    dict(id='g74fd5cdb', field='src', old=None,
         new=['Коммерсантъ (10.08.2026)', 'https://www.kommersant.ru/doc/8876259'],
         quote='«Лента» официально получила контроль над сетью «О\'кей»',
         why='подтверждение контроля по данным СПАРК'),
    dict(id='g74fd5cdb', field='src', old=None,
         new=['BFM Кубань (10.08.2026)', 'https://kuban.bfm.ru/news/60032'],
         quote='Сеть дискаунтеров «Да!» в соглашение не вошла',
         why='структура сделки — без долгов, без сети «Да!», начало ребрендинга'),
]
