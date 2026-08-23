# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), дельта-поиск 23 августа: источники
к gda61c5b8 (Moscow Towers, см. fix_moscow_towers_auction_failed.py),
g948e18e1 (Nordgold, см. fix_nordgold_chukotka_context.py) и gecec7266
(«Салатерия», см. fix_salateria_logistics_constraint.py). Сами факты
дописаны одноразовыми скриптами — здесь только ссылки.

Запуск: python3 pipeline/ingest/review.py --write
"""

FIXES = [
    dict(id='gda61c5b8', field='src', old=None,
         new=['РИА Недвижимость (18.05.2026)', 'https://realty.ria.ru/20260518/auktsion-2093117549.html'],
         quote='не подано ни одной заявки на участие в торгах, в связи с чем процедура проведения торгов не состоялась',
         why='провал майского аукциона'),
    dict(id='gda61c5b8', field='src', old=None,
         new=['Коммерсантъ (18.05.2026)', 'https://www.kommersant.ru/doc/8671762'],
         quote='Начальная цена была установлена на уровне 280,8 млрд руб.',
         why='начальная цена торгов'),
    dict(id='gda61c5b8', field='src', old=None,
         new=['Москва Агентство новостей (19.05.2026)', 'https://www.mskagency.ru/materials/3549153'],
         quote='дисконт в 30% мог бы простимулировать интерес инвесторов',
         why='мнения экспертов о причине провала торгов'),
    dict(id='gda61c5b8', field='src', old=None,
         new=['Rambler Финансы', 'https://finance.rambler.ru/realty/'
              '56935612-arik-shabanov-pochemu-rynok-ne-speshit-pokupat-moscow-towers-dazhe-za-280-8-mlrd-rubley/'],
         quote='Несостоявшийся аукцион показывает, что инвесторы не готовы автоматически принимать заявленную цену',
         why='общий вывод инвестбанкира о провале торгов'),
    dict(id='g948e18e1', field='src', old=None,
         new=['abn.agency (15.07.2026)',
              'https://abn.agency/2026/07/15/'
              'nordgold-alekseya-mordashova-priobrel-kompaniyu-dlya-razrabotki-zolotorudnogo-uchastka-na-chukotke/'],
         quote='ООО «Нордголд Развитие» стало владельцем ООО «Новая сырьевая компания»',
         why='продолжение M&A-активности Nordgold на других рынках'),
    dict(id='gecec7266', field='src', old=None,
         new=['Logistics.ru', 'https://logistics.ru/'
              'produkty-pitaniya-i-fresh-promyshlennost-upravlenie-logistikoy-i-kompaniey/salatnyy-ma-kak-stavka'],
         quote='попытка построить «федерального игрока» сталкивается с физическими ограничениями продукта',
         why='отраслевой скепсис о стратегии консолидации'),
]
