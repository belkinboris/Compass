# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), дельта-поиск 23 августа: источники
к g9fc75a9c (Mixit, см. fix_mixit_2026_expansion.py) и g84fd8194
(Chevron/ЛУКОЙЛ, см. fix_chevron_lukoil_carlyle_update.py). Сами факты
дописаны одноразовыми скриптами — здесь только ссылки.

Запуск: python3 pipeline/ingest/review.py --write
"""

FIXES = [
    dict(id='g9fc75a9c', field='src', old=None,
         new=['Ведомости (04.06.2026)',
              'https://www.vedomosti.ru/business/articles/2026/06/04/1203234-proizvoditel-kosmetiki-mixit'],
         quote='выручка ООО «УК Миксит» выросла на 76,8% до 616,8 млн руб.',
         why='финансовые показатели 2025 года и выход в линейку одежды'),
    dict(id='g9fc75a9c', field='src', old=None,
         new=['Retailer.ru (13.03.2026)',
              'https://retailer.ru/rossijskij-brend-kosmetiki-mixit-zajmetsja-proizvodstvom-i-prodazhej-parfjumerii/'],
         quote='три аромата объемом 50 и 15 мл',
         why='выход в парфюмерию'),
    dict(id='g84fd8194', field='src', old=None,
         new=['Коммерсантъ (24.07.2026)', 'https://www.kommersant.ru/doc/8844173'],
         quote='В январе ЛУКОЙЛ достиг предварительного соглашения о продаже Lukoil International GmbH с американским инвестиционным фондом Carlyle',
         why='подтверждение соглашения ЛУКОЙЛа с Carlyle'),
    dict(id='g84fd8194', field='src', old=None,
         new=['forbes.kz (06.02.2026)',
              'https://forbes.kz/articles/reuters-ucarlyle-poyavilis-soperniki-naaktivy-lukoyla-f26b73'],
         quote='Chevron, а также консорциум с участием Quantum Energy Partners и инвестиционного банка Xtellus Partners',
         why='другие претенденты на портфель наряду с Carlyle'),
    dict(id='g84fd8194', field='src', old=None,
         new=['nationalbusiness.kz (06.02.2026)',
              'https://nationalbusiness.kz/news/chevron-prodolzhaet-peregovori-o-priobretenii-zarubezhnih-aktivov-lukoyla-6e219c/'],
         quote='Как минимум два потенциальных покупателя, включая Chevron, по-прежнему претендуют на приобретение зарубежных активов',
         why='Chevron продолжил переговоры после соглашения с Carlyle'),
    dict(id='g84fd8194', field='src', old=None,
         new=['Zawya (11.03.2026)',
              'https://www.zawya.com/en/projects/oil-and-gas/iraqi-cabinet-approves-west-qurna-2-deal-with-chevron-pfow6mov'],
         quote="Iraq's cabinet has approved the final terms and conditions of the framework agreement",
         why='отдельный трек Chevron — соглашение с Ираком по Западной Курне-2'),
    dict(id='g84fd8194', field='src', old=None,
         new=['The Moscow Times (21.08.2026)',
              'https://ru.themoscowtimes.com/2026/08/21/minfin-ssha-prodlil-litsenziyu-na-prodazhu-zarubezhnykh-aktivov-lukoyla-do-19-sen-a204013'],
         quote='Вашингтон продлил до 19 сентября 2026 года генеральную лицензию',
         why='актуальный статус лицензии OFAC на август 2026'),
]
