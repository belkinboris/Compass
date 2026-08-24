# -*- coding: utf-8 -*-
"""Месячная очередь: источники для fix_glorax_zhilkapinvest_details.py.

Запуск: python3 pipeline/ingest/review.py --write
"""

FIXES = [
    dict(id='g076a2f4e', field='src', old=None,
         new=['РБК Недвижимость', 'https://realty.rbc.ru/news/683d78cf9a7947b3bafa0a26'],
         quote='Мы приобрели серьезного игрока на рынке Владивостока',
         why='интервью президента GloraX с деталями сделки'),
    dict(id='g076a2f4e', field='src', old=None,
         new=['Движение.ру', 'https://dvizhenie.ru/media/3363/fas-soglasovala-pokupku-developerom-glorax-pyati-zastrojshikov-v-primore'],
         quote='Служба рассмотрела ходатайство ООО «Специализированный '
               'Застройщик «Буран»',
         why='точный список пяти юрлиц, согласование ФАС'),
    dict(id='g076a2f4e', field='src', old=None,
         new=['GloraX (пресс-релиз)', 'https://glorax.com/investors/press-center/press-releases/pao-gloraks-zaklyuchilo-soglashenie-o-strategicheskom-sotrudnichestve-s-pao-sberbank'],
         quote='Сбербанк является одним из крупнейших кредиторов '
               'компании',
         why='роль Сбербанка в финансировании сделки'),
]
