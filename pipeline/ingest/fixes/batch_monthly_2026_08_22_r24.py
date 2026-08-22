# -*- coding: utf-8 -*-
"""Месячная очередь, партия 19: источники к
`fix_ipo_monthly_delta_batch1.py` (Озон Фармацевтика, ВсеИнструменты.ру,
IVA Technologies) — сами факты дописаны разовым скриптом, здесь только
ссылки на источники этих фактов.

Запуск: python3 pipeline/ingest/review.py --write
"""

FIXES = [
    dict(id='g41eb17f6', field='src', old=None,
         new=['Sostav.ru',
              'https://www.sostav.ru/publication/ozon-farmatsevtika-'
              'privlekla-2-8-mlrd-rublej-v-khode-vtorichnogo-'
              'razmeshcheniya-aktsij-76029.html'],
         quote='Всего компания разместила 65,9 млн акций и привлекла '
               '2,8 млрд руб. инвестиций.',
         why='источник факта об SPO 2025 года'),
    dict(id='g41eb17f6', field='src', old=None,
         new=['Коммерсантъ', 'https://www.kommersant.ru/doc/8230152'],
         quote='За девять месяцев этого года выручка «Озон '
               'Фармацевтика» увеличилась на 28%, до 21,4 млрд руб.',
         why='источник финансовых показателей за 9 месяцев 2025 года'),
    dict(id='g41eb17f6', field='src', old=None,
         new=['Medvestnik',
              'https://medvestnik.ru/content/news/ozon-farmacevtika-'
              'obyavila-finansovye-i-operacionnye-rezultaty-2025-goda.html'],
         quote='Скорректированная EBITDA 2 увеличилась на 28%, до 12,2 '
               'млрд руб.',
         why='источник финансовых показателей за весь 2025 год '
             '(в исходном тексте после «EBITDA» стоит сносочная цифра «2»)'),

    dict(id='g68ebf773', field='src', old=None,
         new=['Ведомости',
              'https://www.vedomosti.ru/investments/news/2026/07/21/'
              '1215400-aktsii-viru'],
         quote='По состоянию на 16:14 мск 21 июля цена акций '
               '«Всеинструменты.ру» выросла на 7,01% по отношению к '
               'закрытию предыдущего торгового дня и составила 58,29 руб.',
         why='источник факта о цене акции спустя два года после IPO'),
    dict(id='g68ebf773', field='src', old=None,
         new=['Retail.ru',
              'https://www.retail.ru/news/vyruchka-vseinstrumenty-ru-'
              'dostigla-182-9-mlrd-rubley-po-itogam-2025-goda-31-marta-'
              '2026-276142/'],
         quote='Совокупная выручка увеличилась на 7,5% по сравнению с '
               'предыдущим годом, достигнув 182,9 млрд рублей',
         why='источник итогов 2025 года'),
    dict(id='g68ebf773', field='src', old=None,
         new=['Retail.ru',
              'https://www.retail.ru/news/chistaya-pribyl-'
              'vseinstrumenty-ru-prevysila-2-mlrd-rubley-za-kvartal-'
              '17-avgusta-2026-281089/'],
         quote='выручка за первое полугодие увеличилась на 3,2% г/г до '
               '89,6 млрд руб.',
         why='источник итогов первого полугодия 2026 года'),

    dict(id='g5612a3b3', field='src', old=None,
         new=['Коммерсантъ', 'https://www.kommersant.ru/doc/8341837'],
         quote='Ее выручка по итогам 2024 года составила 3,3 млрд руб.',
         why='источник финансовых показателей за 2024 год'),
    dict(id='g5612a3b3', field='src', old=None,
         new=['Ведомости',
              'https://www.vedomosti.ru/investments/news/2026/04/02/'
              '1187533-pribil-iva'],
         quote='Консолидированная выручка группы в прошлом году '
               'сохранилась на уровне предыдущего года и составила 3,2 '
               'млрд руб.',
         why='источник финансовых показателей за 2025 год'),
    dict(id='g5612a3b3', field='src', old=None,
         new=['AK&M',
              'https://www.akm.ru/news/chistyy_ubytok_iva_po_rsbu_za_'
              'i_kvartal_sostavil_230_072_mln_rub/'],
         quote='Чистый убыток ПАО «ИВА» по РСБУ за I квартал 2026 года '
               'составил 230.072 млн руб. против убытка 30.94 млн руб. '
               'годом ранее.',
         why='источник убытка за I квартал 2026 года и падения акций'),
    dict(id='g5612a3b3', field='src', old=None,
         new=['White Square Partners',
              'https://www.whitesquarepartners.com/news/komanda-white-'
              'square-vystupila-yuridicheskim-konsultantom-ipo-iva-'
              'technologies'],
         quote='Практика рынков капитала White Square консультировала '
               'IVA Technologies',
         why='источник факта о юридическом консультанте IPO'),
]
