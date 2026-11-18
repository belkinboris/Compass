# -*- coding: utf-8 -*-
"""Вычитка 18 ноября 2026, партия d18a: стороны по реестру, консультанты из постов фирм, заголовки по стандарту.

gb5c49ac1 («Европолис Ростокино»): второй этап — пересказ Mergers.ru того же заявления Левченко, а не
  переговоры, и заметка обрывалась многоточием; ТЦ — один из двух крупнейших активов Fort Group (ПРАЙМ).
gcc6afd66 (ВТБ/Emperium): 28% без контроля — «Инвестиция»; ККМП представляла продавца (пост ККМП);
  цель сделки была нашим выводом — снята, договоренность на ПМЭФ — фактом в контекст; «впервые зашел в
  судостроение» неверно (ОСК в управлении ВТБ с сентября 2023 года) — снято.
gacef0a9d («Черкизово»/«Вишневский»): заголовок из двух частей — по стандарту; ALUMNI Partners — консультант
  покупателя; одобрение ФАС — в law.appr; род занятий — из финансов в контекст.
g0a1f1895 (Modi): по ЕГРЮЛ (datanewton, ОГРН 1177746360901) 17 мая 2024 года 100% ООО «Моди» перешли от
  кипрской Lonago Enterprises Ltd. к ООО «ГИ-2» (Владимир Палий, владелец «ГЕМ Инвеста») — стороны по
  реестру; Инна Сухотина — бенефициар, в law.struct.
g627ecd3f (Таганрогский терминал): продавец — ООО «Рэвард Инвест» (Коммерсантъ: «ранее обе компании
  принадлежали»), Раппопорт — в law.struct; BIRCH LEGAL — консультант покупателя; цель — со слов источника.
gde2618e8 (Purmo): продан весь российский бизнес, а не «контролирующий пакет»; предмет — две компании из
  годового отчета Purmo за 2023 год; согласование подкомиссии — в law.appr.
g60130b7f («Прогресс»): ККМП — консультант покупателя; механика контроля (АО «Прогресс Капитал», Алексей
  Мельник) — в law.struct; финансы — в target_fin; описание «Румелко» без чужой доли.
g9e9c96fd («Времена года»): механика сделки вместо описания работы юристов; оценка без автора — без
  выдуманных «участников рынка».
g05d87236 (Gallina Blanca): первоисточник — Ведомости; ALUMNI Partners — консультант продавца; ЕГРЮЛ.
g0c7ad0fb (Everdom): заголовок без имени человека; вторая оценка затрат; «первый проект» не подтвержден;
  цель — словами гендиректора фонда; Bright Rich | CORFAC International — консультант сделки.

    python3 pipeline/archive/2026-11/reread_oneoff_d18a.py [--write]
"""
import copy
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY, DAY = 'reread_oneoff_d18a', '2026-11-18'
UNSET = object()

PRIME_FORT = 'https://1prime.ru/20261113/vladelets-875211218.html'
MERGERS_FORT = 'https://mergers.ru/news/Fort-Group-rassmotrit-vozmozhnost-prodazhi-TC-Evropolis-Rostokino-87801'
PRIME_VTB = 'https://1prime.ru/20231229/842712265.html'
KKMP_VTB = 'https://t.me/kkmpconnect/1384'
MAIL_VTB = 'https://finance.mail.ru/article/gruppa-vtb-priobrela-28-proizvoditelya-rossiyskih-elektrosudov-emperium-59210137/'
ALUMNI_CH = 'https://t.me/alumnipartnerslawfirm/333'
PRIME_CH = 'https://1prime.ru/20221027/838612885.html'
K_MODI = 'https://www.kommersant.ru/doc/6714047'
DN_MODI = 'https://datanewton.ru/api/v2/history?ogrn=1177746360901&startDate=2000-01-01&attributes=OWNERS'
ALUMNI_MODI = 'https://t.me/alumnipartnerslawfirm/1175'
K_TZT = 'https://www.kommersant.ru/doc/6852573'
BIRCH_TZT = 'https://t.me/BIRCHLEGAL/1050'
PURMO_SOLD = 'https://www.purmogroup.com/?p=3893'
PURMO_AR = 'https://www.purmogroup.com/wp-content/uploads/2024/03/Purmo_Group_Annual_Report_2023_19032024.pdf'
BIRCH_PURMO = 'https://t.me/BIRCHLEGAL/1159'
KKMP_PROG = 'https://t.me/kkmpconnect/2091'
DAIRY_PROG = 'https://dairynews.today/kz/news/kholding-rumelko-priobrel-ao-progress-proizvoditelya-brenda-frutonyanya.html'
SOSTAV_PROG = 'https://www.sostav.ru/publication/proizvoditel-frutonyani-obrel-novogo-kontroliruyushchego-aktsionera-74428.html'
RETAIL_PROG = 'https://www.retail.ru/news/struktura-vladimira-lisina-priobrela-vladeltsa-brendov-frutonyanya-i-lipetskiy-b-1-oktyabrya-2024-245690/'
NR_VG = 'https://new-retail.ru/novosti/retail/moskovskiy_tts_vremena_goda_smenil_vladeltsa/'
VED_GB = 'https://www.vedomosti.ru/business/articles/2022/10/25/947363-galina-blanca-kupil-vladelets-doshiraka'
ALUMNI_GB = 'https://t.me/alumnipartnerslawfirm/329'
SNOB_GB = 'https://snob.ru/news/korejskij-vladelec-doshiraka-kupil-proizvoditelya-gallina-blanca/'
K_EVER = 'https://kommersant.ru/doc/8081357'
ALUMNI_EVER = 'https://t.me/alumnipartnerslawfirm/2230'
RETAIL_EVER = 'https://www.retail.ru/news/na-yuge-moskvy-poyavitsya-krupnyy-skladskoy-kompleks-3-oktyabrya-2025-269833/'

Q_MODI_REG = ('ЕГРЮЛ, ООО «Моди» (ОГРН 1177746360901): 2017-08-25 ЛОНАГО ЭНТЕРПРАЙЗИС ЛИМИТЕД — 100%; '
              '2024-05-17 left ЛОНАГО ЭНТЕРПРАЙЗИС ЛИМИТЕД (100 → None); 2024-05-17 joined ООО "ГИ-2" '
              '(ОГРН 1237700698201) (None → 100). Коммерсантъ: «Юридически компания продолжила принадлежать '
              'кипрской Lonago Enterprises Ltd.»')

EDITS = [
    # ---- gb5c49ac1
    dict(id='gb5c49ac1', path='events.1', old={
        'kind': 'negotiations', 'date': '2026-11-17', 'title': 'Переговоры',
        'note': 'Владелец крупного торгового центра "Европолис Ростокино" на северо-востоке Москвы Максим Левченко '
                'объявил о готовности его продать. "С этим местом связаны несколько насыщенных лет моей жизни. '
                'Теперь у нас другие планы, и мы готовы обсуждать продажу…',
        'source': ['Mergers.ru', MERGERS_FORT]},
        new={'kind': 'other', 'date': '2026-11-17', 'title': 'Повторное сообщение о продаже',
             'note': 'Mergers.ru пересказал заявление Максима Левченко о готовности обсуждать продажу '
                     'ТЦ «Европолис Ростокино»; покупатель и цена не названы.',
             'source': ['Mergers.ru', MERGERS_FORT]}),
    dict(id='gb5c49ac1', path='law.struct',
         sub=('Торговый центр — крупнейший актив девелопера Fort Group',
              'Торговый центр — один из двух крупнейших активов девелопера Fort Group')),
    # ---- gcc6afd66
    dict(id='gcc6afd66', path='type', old='M&A', new='Инвестиция'),
    dict(id='gcc6afd66', path='asset', old='28% в дочерней компании Emperium', new='Emperium',
         quote='Группа ВТБ вошла в судостроительный бизнес Sitronics Group и приобрела долю в 28% в капитале ее '
               'дочерней компании Emperium, управляющей производством электросудов', url=PRIME_VTB),
    dict(id='gcc6afd66', path='eco.share', old='—', new='28% в капитале Emperium',
         quote='Группа ВТБ вошла в судостроительный бизнес Sitronics Group и приобрела долю в 28% в капитале ее '
               'дочерней компании Emperium', url=PRIME_VTB),
    dict(id='gcc6afd66', path='law.adv', old=[], new=[['Юридический консультант продавца (Sitronics Group)', 'ККМП']],
         quote='Команда юристов ККМП представляла интересы Sitronics Group в сделке по продаже 28% долей в компании '
               'Emperium, управляющей производством электросудов, в пользу Группы ВТБ.', url=KKMP_VTB),
    dict(id='gcc6afd66', path='eco.rationale',
         old='Банк и Sitronics Group договорились о финансировании развития российских электросудов еще на ПМЭФ-2023; '
             'покупка доли в Emperium продолжает эту договоренность и вводит ВТБ в судостроительный бизнес группы.',
         new='—'),
    dict(id='gcc6afd66', path='eco.target_fin',
         old='У Emperium несколько моделей электросудов — среди них однопалубный речной Ecobus, двухпалубный '
             'прогулочный катамаран Ecocruiser и электрическая версия теплохода «Москва 2.0». Вместимость судов '
             'разных классов — от 50 до 200 человек. Маршруты в Москве, Нижнем Новгороде и Красноярске эти суда '
             'обслуживают с прошлого лета.',
         new='—'),
    dict(id='gcc6afd66', path='eco.context',
         old='Планы компании простираются до 2025 года: на отрадненской площадке должны появиться новый эллинг и '
             'стационарный подъемно-спусковой комплекс, плюс новые цеха под обработку корпусов. Параллельно идет '
             'модернизация пермской верфи. Если обе площадки выйдут на полную мощность, через два-три года '
             'совокупный выпуск должен достичь 40 судов ежегодно.',
         new='Emperium строит пассажирские электросуда вместимостью от 50 до 200 человек: речные однопалубные Ecobus, '
             'прогулочные катамараны Ecocruiser, электрическую версию теплохода «Москва 2.0». Летом 2023 года они '
             'вышли на маршруты в Москве, Нижнем Новгороде и Красноярске. Договоренность о финансировании '
             'электросудостроения появилась еще на ПМЭФ-2023.\n\n'
             'Sitronics Group рассчитывала к 2025 году расширить верфь в Отрадном — построить новый эллинг, '
             'стационарный подъемно-спусковой комплекс, корпусные и механические цеха — и модернизировать Пермскую '
             'судоверфь, чтобы за два-три года выйти на выпуск до 40 судов в год на обеих площадках.'),
    dict(id='gcc6afd66', path='events.0.note',
         old='Доля перешла от Sitronics Group к банковской группе — так ВТБ впервые зашел в судостроение.',
         new='Доля 28% в Emperium перешла от Sitronics Group к группе ВТБ.'),
    # ---- gacef0a9d
    dict(id='gacef0a9d', path='title',
         old='«Черкизово» купило СГЦ «Вишневский»: 99% получила одна дочерняя компания холдинга, 1% — другая',
         new='«Черкизово» купило СГЦ «Вишневский»',
         quote='Группа "Черкизово", один из крупнейших производителей мяса и мясных продуктов в РФ, приобрела '
               'селекционно-генетический центр "Вишневский"', url=PRIME_CH),
    dict(id='gacef0a9d', path='law.adv', old=[], new=[['Юридический консультант покупателя', 'ALUMNI Partners']],
         quote='Команда ALUMNI Partners успешно завершила юридическое сопровождение Группы «Черкизово» в связи с '
               'приобретением селекционно-генетического центра «Вишневский» в Оренбургской области.', url=ALUMNI_CH),
    dict(id='gacef0a9d', path='law.appr', old='—', new='Сделку одобрила ФАС.',
         quote='Сделка уже получила одобрение Федеральной антимонопольной службы', url=PRIME_CH),
    dict(id='gacef0a9d', path='eco.target_fin',
         old='Мощность всех пяти площадок «Вишневского» — больше 250 тысяч голов в год; центр работает с 2006 года '
             'и держит как чистопородных свиней (йоркшир, дюрок, ландрас), так и гибридов F1, а заодно занимается '
             'товарным свиноводством и мясным производством.',
         new='Мощность пяти площадок «Вишневского» — больше 250 тысяч голов в год.'),
    dict(id='gacef0a9d', path='eco.context',
         old='Через месяц после сделки «Черкизово» объявило о 500 млн рублей инвестиций в модернизацию '
             '«Вишневского»: по плану это должно поднять выпуск генетического материала на сорок процентов и '
             'полностью закрыть собственную потребность холдинга в нем.',
         new='СГЦ «Вишневский» основан в 2006 году в Оренбургской области: разводит чистопородных свиней (йоркшир, '
             'дюрок, ландрас) и гибридов F1, занимается товарным свиноводством и выпускает мясную продукцию.\n\n'
             'Через месяц после сделки «Черкизово» объявило о 500 млн рублей инвестиций в модернизацию '
             '«Вишневского»: по плану это должно поднять выпуск генетического материала на сорок процентов и '
             'полностью закрыть собственную потребность холдинга в нем.'),
    # ---- g0a1f1895
    dict(id='g0a1f1895', path='seller', old='Инна Сухотина (основная наследница, бенефициар Modi — отчет ООО «Моди»)',
         new='Lonago Enterprises Ltd.', retract=True, quote=Q_MODI_REG, url=DN_MODI),
    dict(id='g0a1f1895', path='buyer', old='g0e89d473', new='__DEL__', quote=Q_MODI_REG, url=DN_MODI),
    dict(id='g0a1f1895', path='buyer_name', old=None, new='ООО «ГИ-2»',
         quote='ООО «ГИ-2» 17 мая стало единственным владельцем ООО «Моди», управляющего сетью магазинов Modi',
         url=K_MODI),
    dict(id='g0a1f1895', path='title', old='«ГЕМ Инвест» купил сеть Modi у наследников Игоря Сосина',
         new='«ГИ-2» купил сеть Modi',
         quote='ООО «ГИ-2» 17 мая стало единственным владельцем ООО «Моди», управляющего сетью магазинов Modi',
         url=K_MODI),
    dict(id='g0a1f1895', path='eco.share', old='Доля в ООО «Моди»', new='100% доли в ООО «Моди»',
         quote='ООО «ГИ-2» 17 мая стало единственным владельцем ООО «Моди»', url=K_MODI),
    dict(id='g0a1f1895', path='law.adv', old=[['Юристы', 'ALUMNI Partners']],
         new=[['Юридический консультант покупателя', 'ALUMNI Partners']],
         quote='Команда ALUMNI Partners выступила юридическим консультантом структуры инвестиционной компании '
               '«ГЕМ Инвест» в рамках сделки по приобретению ООО «Моди»', url=ALUMNI_MODI),
    dict(id='g0a1f1895', path='law.struct',
         old='По документам покупатель — ООО «ГИ-2»: 99,99% у Владимира Палия, 0,01% у Марии Мамонтовой. '
             '«ГЕМ Инвест» подтвердил факт покупки, но сумму не назвал.',
         new='Владельцы ООО «ГИ-2» — Владимир Палий, хозяин инвесткомпании «ГЕМ Инвест» (99,99%), и Мария Мамонтова '
             '(0,01%); в «ГЕМ Инвесте» покупку подтвердили, сумму не назвали. Продавец по ЕГРЮЛ — кипрская Lonago '
             'Enterprises Ltd., которой ООО «Моди» принадлежало с 2017 года; после смерти Игоря Сосина '
             'бенефициаром сети стала его основная наследница Инна Сухотина.'),
    dict(id='g0a1f1895', path='eco.context',
         sub=('а купленный сейчас актив не включает', 'а проданный актив не включает')),
    dict(id='g0a1f1895', path='date_basis', old=None, new='registry'),
    dict(id='g0a1f1895', path='party_evidence.buyer', old=UNSET, new=[
        {'value': 'ООО "ГИ-2"', 'field': 'buyer_name', 'method': 'registry_owner_history', 'url': DN_MODI}]),
    dict(id='g0a1f1895', path='party_evidence.seller', old=UNSET, new=[
        {'value': 'ЛОНАГО ЭНТЕРПРАЙЗИС ЛИМИТЕД', 'field': 'seller', 'method': 'registry_owner_history', 'url': DN_MODI}]),
    dict(id='g0a1f1895', path='accepted_notes.no_profile.seller', old=UNSET,
         new='Продавец по ЕГРЮЛ — кипрская Lonago Enterprises Ltd. (ЛОНАГО ЭНТЕРПРАЙЗИС ЛИМИТЕД), участник ООО «Моди» '
             'со 100% с 2017 года до 17 мая 2024 года (datanewton, ОГРН 1177746360901); Коммерсантъ: «Юридически '
             'компания продолжила принадлежать кипрской Lonago Enterprises Ltd.». Иностранное юрлицо, профиля нет. '
             'Инна Сухотина — бенефициар по отчету ООО «Моди», в law.struct.'),
    dict(id='g0a1f1895', path='accepted_notes.no_profile.buyer', old=None,
         new='Покупатель по ЕГРЮЛ — ООО «ГИ-2» (ОГРН 1237700698201), вошло 17 мая 2024 года со 100% (datanewton); '
             'его владелец Владимир Палий — хозяин «ГЕМ Инвеста» (Коммерсантъ), это в law.struct. Профиля «ГИ-2» в '
             'базе нет, оставлено текстом; профиль «ГЕМ Инвест» со стороны снят — в реестр вошел не он.'),
    dict(id='g0a1f1895', path='accepted_notes.no_inn.target', old=UNSET,
         new='ОГРН ООО «Моди» — 1177746360901 (audit-it, datanewton: история участников Сосин → Lonago → «ГИ-2» '
             'совпадает с Коммерсантом); ИНН 9718057899 виден только в выдаче audit-it (страница закрыта для '
             'запросов), второго независимого источника нет — ИНН не ставим.'),
    dict(id='g0a1f1895', path='retracted.buyer_name', old=UNSET, new=['«ГЕМ Инвест»', 'ООО «ГЕМ Инвест»']),
    # ---- g627ecd3f
    dict(id='g627ecd3f', path='seller', old='Александр Раппопорт (ООО «Рэвард Инвест»)', new='ООО «Рэвард Инвест»',
         retract=True,
         quote='Ранее обе компании принадлежали ООО «Рэвард Инвест», чьим бенефициаром является Александр Раппопорт.',
         url=K_TZT),
    dict(id='g627ecd3f', path='title',
         old='«Евразия-Логистика» купила 90,59% ООО «Таганрогский зерновой терминал» и ООО «ТСРЗ» у Александра Раппопорта',
         new='«Евразия-Логистика» купила 90,59% Таганрогского зернового терминала',
         quote='Компания «Евразия логистика», специализирующаяся на перевозках зерна, приобрела 90,59% долей в ООО '
               '«Таганрогский зерновой терминал» (ТЗТ) и ООО «ТСРЗ» 25 июля 2024 года.',
         url='https://runews24.ru/business/26/07/2024/perevozchik-zerna-evraziya-logistika-priobrel-taganrogskij-zernovoj-terminal'),
    dict(id='g627ecd3f', path='law.adv', old=[], new=[['Юридический консультант покупателя', 'BIRCH LEGAL']],
         quote='Команда BIRCH LEGAL оказала комплексное юридическое сопровождение сделки по приобретению '
               'Таганрогского зернового терминала логистической компанией Евразия-Логистика.', url=BIRCH_TZT),
    dict(id='g627ecd3f', path='law.struct', old='—',
         new='До сделки обе компании принадлежали ООО «Рэвард Инвест»; его бенефициар — Александр Раппопорт.'),
    dict(id='g627ecd3f', path='eco.rationale',
         old='«Евразия-Логистика» перевозит зерно по железной дороге, и терминал в Таганроге дает ей свою точку '
             'выхода груза на экспорт, а не зависимость от чужих мощностей. Александр Раппопорт, напротив, выходит '
             'из зернового бизнеса, говорят источники, близкие к сторонам сделки.',
         new='По неофициальным данным, терминал понадобился владельцу «Евразия-Логистики» Илье Желнову для '
             'развития транспортных активов, а Александр Раппопорт решил продать актив и перестать торговать зерном.'),
    dict(id='g627ecd3f', path='party_evidence.seller', old=UNSET, new=[
        {'value': 'ООО «Рэвард Инвест»', 'field': 'seller', 'method': 'source_statement', 'url': K_TZT}]),
    dict(id='g627ecd3f', path='accepted_notes.no_profile.seller', old=UNSET,
         new='Продавец — ООО «Рэвард Инвест»: Коммерсантъ со ссылкой на ЕГРЮЛ — «Ранее обе компании принадлежали ООО '
             '«Рэвард Инвест», чьим бенефициаром является Александр Раппопорт». Профиля в базе нет, оставлено '
             'текстом; Раппопорт — в law.struct.'),
    # ---- gde2618e8
    dict(id='gde2618e8', path='title',
         old='Purmo Group передала контролирующий пакет российского бизнеса российской инвесткомпании',
         new='Российская инвесткомпания купила российский бизнес Purmo Group',
         quote='Purmo Group has today on 11 September 2024 sold its Russian operations to a Russian investment company.',
         url=PURMO_SOLD),
    dict(id='gde2618e8', path='asset', old='две дочерние компании, производящие радиаторы',
         new='ZAO EVRA Varme RUS и Evroradiators LLC',
         quote='Purmo Group Annual Report 2023, group companies: ZAO EVRA Varme RUS | Russia | Sales | 100; '
               'Evroradiators LLC Russia¹ | Russia | Production and sales | 51 (¹ 100% owned by Euroradiators '
               'Holding B.V). BIRCH LEGAL: «сделки по продаже двух дочерних компаний Purmo Group, занимающихся '
               'производством и продажей радиаторов»', url=PURMO_AR),
    dict(id='gde2618e8', path='events.0.note',
         old='Purmo Group передала контролирующий пакет двух дочерних компаний, производящих радиаторы, неназванной '
             'российской инвесткомпании.',
         new='Purmo Group продала российский бизнес — две компании по производству и продаже радиаторов — '
             'неназванной российской инвестиционной компании; цену стороны договорились не раскрывать.'),
    dict(id='gde2618e8', path='law.struct',
         old='BIRCH LEGAL была юридическим консультантом продавца, Purmo Group: вела тендер среди покупателей, '
             'проводила vendor due diligence, готовила документы по сделке и представляла Purmo Group на переговорах. '
             'Отдельно команда добивалась согласования сделки у подкомиссии по контролю за иностранными инвестициями в РФ.',
         new='Purmo Group продала российский бизнес целиком и после сделки не работает в России. По годовому отчету '
             'группы за 2023 год, в России ей принадлежали ZAO EVRA Varme RUS (продажи, 100%) и Evroradiators LLC '
             '(производство и продажи; ею владела Euroradiators Holding B.V., где у Purmo 51%). Покупателю перешли '
             'доли и акции российских компаний; покупателя искали через тендер, его название не раскрыто.'),
    dict(id='gde2618e8', path='law.appr', old='—',
         new='Сделку согласовывала подкомиссия правительственной комиссии по контролю за осуществлением иностранных '
             'инвестиций.',
         quote='Кроме того, мы сопровождали согласование сделки в подкомиссии по контролю за осуществлением '
               'иностранных инвестиций в Российской Федерации.', url=BIRCH_PURMO),
    dict(id='gde2618e8', path='party_evidence.target', old=UNSET, new=[
        {'value': 'ZAO EVRA Varme RUS и Evroradiators LLC', 'field': 'asset', 'method': 'source_statement',
         'url': PURMO_AR}]),
    dict(id='gde2618e8', path='accepted_notes.no_profile.target', old=UNSET,
         new='Предмет — две российские компании Purmo Group по годовому отчету группы за 2023 год: ZAO EVRA Varme RUS '
             '(продажи) и Evroradiators LLC (производство и продажи, через Euroradiators Holding B.V.). Других '
             'российских компаний в отчете нет, BIRCH LEGAL пишет о продаже двух дочерних компаний (долей и акций). '
             'Русские названия юрлиц в источниках о сделке не приводятся — профили не заводили.'),
    # ---- g60130b7f
    dict(id='g60130b7f', path='title',
         old='«Румелко» купил контролирующий пакет АО «Прогресс» (бренды «ФрутоНяня» и «Липецкий бювет»)',
         new='«Румелко» купил контролирующий пакет «Прогресса»',
         quote='Команда юристов ККМП представляла интересы покупателя в сделке по приобретению контролирующего '
               'пакета акций в АО «ПРОГРЕСС»', url=KKMP_PROG),
    dict(id='g60130b7f', path='law.adv', old=[], new=[['Юридический консультант покупателя', 'ККМП']],
         quote='Команда юристов ККМП представляла интересы покупателя в сделке по приобретению контролирующего '
               'пакета акций в АО «ПРОГРЕСС»', url=KKMP_PROG),
    dict(id='g60130b7f', path='law.struct',
         old='Юридическую сторону сделки для «Румелко» закрывала команда ККМП во главе с управляющим партнером '
             'Максимом Кулешовым — она вела все транзакционные вопросы покупки контролирующего пакета «Прогресса».',
         new='Контроль перешел через АО «Прогресс Капитал», которому принадлежит «Прогресс»: по отчетности за '
             '2024 год, с 1 ноября 2024 года контролирующим акционером обеих компаний стал Алексей Мельник — через '
             'свои компании он держит больше половины акций «Прогресс Капитала». До августа 2024 года Мельник '
             'руководил «Румелкоагро-молоко» из агрохолдинга Владимира Лисина «Румелко».'),
    dict(id='g60130b7f', path='eco.target_fin', old='—',
         new='Выручка «Прогресса» в 2023 году — почти 38 млрд руб. (плюс 14,7% за год), чистая прибыль — 6,4 млрд руб.; '
             'в 2024 году выручка выросла на 27%, до 48,2 млрд руб., прибыль — на 26%, до 8 млрд руб.'),
    dict(id='g60130b7f', path='eco.context',
         sub=(' Выручка «Прогресса» в 2023 году составила почти 38 млрд руб. (рост на 14,7% год к году) при чистой '
              'прибыли 6,4 млрд руб.; уже при новом акционере, в 2024 году, выручка поднялась на 27%, до 48,2 млрд '
              'руб., а прибыль — на 26%, до 8 млрд руб.', '')),
    dict(id='g60130b7f', path='eco.val',
         old='Официально сумму сделки не раскрыли ни одна из сторон. Управляющий партнер Walnut Capital Артем '
             'Моторный предполагает, что «Прогресс» стоил 80–85 млрд руб.',
         new='Официально сумму сделки не раскрыли ни одна из сторон; по неофициальным данным, она могла составить '
             'около 70 млрд руб. Управляющий партнер Walnut Capital Артем Моторный предполагает, что «Прогресс» '
             'стоил 80–85 млрд руб.'),
    dict(id='g60130b7f', path='companies.g515248f7.desc',
         old='Агрохолдинг Владимира Лисина, основного владельца НЛМК: молочное животноводство и выращивание кормов в '
             'Тверской и Калужской областях и Алтайском крае. Владеет 21,51% ООО «Румелко-Агро».',
         new='Агрохолдинг Владимира Лисина, основного владельца НЛМК: молочное животноводство и выращивание кормов в '
             'Тверской и Калужской областях и Алтайском крае.'),
    # ---- g9e9c96fd
    dict(id='g9e9c96fd', path='law.struct',
         old='ККМП вела для «Кэпитал менеджмент» разработку транзакционных документов по сделке.',
         new='Предмет сделки — ООО «Октан плюс альфа», которому принадлежит торговый центр «Времена года» на '
             'Кутузовском проспекте; его продала люксембургская RD Property Holdings. «Кэпитал менеджмент» учредили '
             'Дмитрий Чурин (99%) и Вадим Ковалев (1%), партнеры юрфирмы CLS. По неофициальным данным, после '
             'сделки владелец комплекса перешел из люксембургской юрисдикции в российскую, а новыми собственниками '
             'стали топ-менеджеры RD Group.'),
    dict(id='g9e9c96fd', path='eco.context',
         sub=(' Неофициально сделка сопровождалась редомициляцией владельца комплекса — переводом собственника из '
              'люксембургской юрисдикции в российскую.', '')),
    dict(id='g9e9c96fd', path='eco.val',
         old='Цену самой сделки стороны не раскрыли. По оценке участников рынка, рыночная стоимость объекта '
             'составляла 25–27 млрд руб.; к цене сделки эту оценку приравнивать нельзя.',
         new='Цену самой сделки стороны не раскрыли. Рыночную стоимость объекта оценивали в 25–27 млрд руб. (автор '
             'оценки не назван); это не цена сделки.'),
    # ---- g05d87236
    dict(id='g05d87236', path='law.adv', old=[], new=[['Юридический консультант продавца (The GBFoods)', 'ALUMNI Partners']],
         quote='Команда ALUMNI Partners успешно завершила юридическое сопровождение The GBFoods S.A. в сделке по '
               'продаже ее производственного и дистрибьютерского бизнеса в России и СНГ в пользу HYSG Group.',
         url=ALUMNI_GB),
    dict(id='g05d87236', path='law.struct', old='—',
         new='По данным ЕГРЮЛ, сделку закрыли 25 октября 2022 года: из учредителей «Юроп Фудс ГБ» вышли испанские '
             'компании GBFoods «Препаратос Алиментисиос С.А.» и «Сугеме С.А.», вошла HYSG Pte. Ltd. (в ЕГРЮЛ — '
             '«Эйчуайэсджи Пте. Лтд.»). HYSG Group стала единственным акционером, гендиректором назначен Рю Тэджун.'),
    # ---- g0c7ad0fb
    dict(id='g0c7ad0fb', path='title', old='Фонд Ольги Белявцевой покупает склад у NK Group',
         new='Evermount Capital Group покупает склад Everdom у NK Group',
         quote='Девелопер NK Group построит для фонда частных активов Evermount Capital Group складской комплекс '
               'Everdom в логистическом парке «NK Домодедово-1 ».', url=RETAIL_EVER),
    dict(id='g0c7ad0fb', path='eco.val',
         old='Официальную сумму инвестиций не называли; аналитик — инвестиционный директор УК «Тетис Кэпитал» Ольга '
             'Селюгина — оценивает затраты на строительство склада в 4–4,5 млрд руб.',
         new='Официальную сумму инвестиций не называли. Затраты фонда на строительство склада инвестиционный '
             'директор УК «Тетис Кэпитал» Ольга Селюгина оценивает в 4–4,5 млрд руб., директор департамента '
             'складской и промышленной недвижимости Remain Александр Федоров — в 4,5–5 млрд руб.'),
    dict(id='g0c7ad0fb', path='eco.context',
         old='До этой сделки фонд инвестировал в основном в FMCG, питание, фудтех и агросектор — склад стал его '
             'первым проектом в складской недвижимости. Руководит фондом гендиректор Антон Чертков.',
         new='Evermount Capital Group вкладывает деньги в проекты в сфере FMCG, питания, фудтеха и агросектора; фонд '
             'принадлежит Ольге Белявцевой. Руководит им гендиректор Антон Чертков.'),
    dict(id='g0c7ad0fb', path='eco.rationale', old='—',
         new='Гендиректор Evermount Capital Group Антон Чертков объясняет решение тем, что складская недвижимость '
             '«обладает коротким сроком строительства и может обеспечить гарантированный денежный поток».'),
    dict(id='g0c7ad0fb', path='law.adv', old=[['Юридический консультант покупателя', 'ALUMNI Partners']],
         new=[['Юридический консультант покупателя', 'ALUMNI Partners'],
              ['Консультант по сдаче склада в аренду', 'Bright Rich | CORFAC International']],
         quote='Сделку сопровождала компания Bright Rich | Corfac International, которая стала эксклюзивным '
               'консультантом по сдаче складского комплекса в аренду.', url=RETAIL_EVER),
]
# Источники: новая строка встает (first=True — первой, иначе последней)
SRC = [
    ('g05d87236', ['Ведомости, «Производителя Gallina Blanca купил корейский владелец «Доширака»» (25.10.2022)', VED_GB], True),
    ('g0c7ad0fb', ['Retail.ru, «На юге Москвы появится крупный складской комплекс» (03.10.2025)', RETAIL_EVER], False),
    ('gde2618e8', ['Purmo Group, годовой отчет за 2023 год', PURMO_AR], False),
    ('g0a1f1895', ['История участников ЕГРЮЛ ООО «Моди» (datanewton)', DN_MODI], False),
]


def _walk(root, path, create=False):
    parts = path.split('.')
    cur = root
    for p in parts[:-1]:
        if isinstance(cur, list):
            cur = cur[int(p)]
        else:
            if p not in cur:
                if not create:
                    return None, parts[-1]
                cur[p] = {}
            cur = cur[p]
    return cur, parts[-1]


def _get(c, path):
    parent, last = _walk(c, path)
    if parent is None:
        return None
    if isinstance(parent, list):
        return parent[int(last)]
    return parent.get(last)


def _set(c, path, v):
    parent, last = _walk(c, path, create=True)
    if isinstance(parent, list):
        parent[int(last)] = v
    else:
        parent[last] = v


def apply(data):
    by = {d['id']: d for d in data['deals']}
    n = 0
    for e in EDITS:
        c = by[e['id']]
        target, path = c, e['path']
        if path.startswith('companies.'):
            _, cid, field = path.split('.', 2)
            target, path = data['companies'][cid], field
        cur = _get(target, path)
        if 'sub' in e:
            a, b = e['sub']
            if a not in (cur or '') and (b == '' or b in (cur or '')):
                continue
            assert cur and cur.count(a) == 1, (e['id'], e['path'], cur)
            _set(target, path, cur.replace(a, b))
            n += 1
            continue
        if e['new'] == '__DEL__':
            if cur is None:
                continue
            assert cur == e['old'], (e['id'], e['path'], cur)
            del target[path]
            if e.get('quote'):
                fact_edit_guard.log(c, path, None, e['quote'], e['url'], BY, DAY)
            n += 1
            continue
        if cur == e['new']:
            continue
        if e['old'] is not UNSET:
            assert cur == e['old'], (e['id'], e['path'], cur)
        _set(target, path, copy.deepcopy(e['new']))
        if e.get('retract') and e['old'] not in (None, 'Не раскрыта'):
            lst = c.setdefault('retracted', {}).setdefault(path, [])
            if e['old'] not in lst:
                lst.append(e['old'])
        if e.get('quote'):
            fact_edit_guard.log(c, path, e['new'], e['quote'], e['url'], BY, DAY)
        n += 1
    for cid, row, first in SRC:
        c = by[cid]
        if any(s[1] == row[1] for s in c['src']):
            continue
        if first:
            c['src'].insert(0, row)
        else:
            c['src'].append(row)
        n += 1
    return n


def main(write):
    raw = open(DATA, encoding='utf-8').read()
    old, data = json.loads(raw), json.loads(raw)
    n = apply(data)
    if not n:
        print('Уже применено.')
        return 0
    mass_edit_guard.check(old, data, os.environ.get('MASS_OK'))
    bad = fact_edit_guard.unbacked(old, data)
    assert not bad, bad
    if not write:
        print('Сухой прогон: %d правок. Запись — с ключом --write.' % n)
        return 0
    fresh_raw = open(DATA, encoding='utf-8').read()
    fresh = json.loads(fresh_raw)
    apply(fresh)
    with open(DATA, 'w', encoding='utf-8') as f:
        f.write(json.dumps(fresh, ensure_ascii=False, indent=1) + ('\n' if fresh_raw.endswith('\n') else ''))
    print('ЗАПИСАНО: %d правок.' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
