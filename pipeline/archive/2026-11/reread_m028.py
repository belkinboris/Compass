# -*- coding: utf-8 -*-
"""Вычитка базы, марафон 12 ноября 2026, партия m028: правки, которые не ложатся в таблицу FIXES.

ЧТО ЧИНИТ. Поля-факты, подтвержденные реестром (дата перехода доли, продавец по истории
участников ЕГРЮЛ), снятие неподтвержденных значений (оценки без автора и источника),
доля, заголовок по стандарту (`pipeline/title_standard.py`) и тексты профилей. Каждая
правка факта несет цитату источника (`fact_edit_guard.log`), перед записью стоит `assert`
на старое значение; повторный запуск пропускает уже примененное.

ПОЧЕМУ НЕ review.py. Дата из реестра не названа в статье прописью (review.py такую дату не
принимает), заглушки и снятие значений таблица не переносит, профили она не правит.

    python3 pipeline/archive/2026-11/reread_m028.py            # сухой прогон
    python3 pipeline/archive/2026-11/reread_m028.py --write    # запись (делает reread_apply.py)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
DAY, BY = '2026-11-12', 'reread_m028'
FACT = set(fact_edit_guard.FACT_FIELDS)

# Правки карточек: id, поле (через точку: eco.val), старое, новое, цитата, адрес.
EDITS = []
# Правки профилей: id профиля, ключ, старое, новое.
COMPANY = []
# Снятые значения — в retracted, чтобы обогащение их не вернуло: id, поле, значение.
RETRACT = []
# Ключи сопоставления профилей (match_keys): id профиля, ключ.
MATCH = []

# --- данные партии ---
RBC_AVA = 'https://kuban.rbc.ru/krasnodar/freenews/66ebc82c9a79474f7dfcdee7'
REG_AVA = 'https://datanewton.ru/api/v2/history?ogrn=1162375022699&startDate=2024-01-01&attributes=OWNERS'
Q_REG_AVA = ('ЕГРЮЛ, участники ООО «АВА ДОМ» (ОГРН 1162375022699), запись от 2024-10-02: АРУТЮНЯН ВАГАН АРСЕНОВИЧ '
             '100% (400 011 111 руб.) -> 50% (200 005 555,5 руб.); добавлен КРЕМЛЕВ УМАР НАЗАРОВИЧ 50% '
             '(200 005 555,5 руб.); уставный капитал не менялся.')
EDITS = [
 # g6bf4b33c Кремлев / AVA Group
 dict(id='g6bf4b33c', field='title', old='Умар Кремлев приобрел 50% AVA Group', new='Умар Кремлев купил 50% AVA Group',
      quote='Умар Кремлев стал совладельцем компании AVA Group с долей 50%', url=RBC_AVA),
 dict(id='g6bf4b33c', field='date', old='2024-09-19', new='2024-10-02', quote=Q_REG_AVA, url=REG_AVA),
 dict(id='g6bf4b33c', field='eco.share', old='—', new='50% доли в ООО «Ава Дом»',
      quote='В соответствии с договоренностями каждый из них будет владеть равной долей в размере 50% компании AVA Group',
      url=RBC_AVA),
 # оценка 15–17 млрд ₽ и «безденежная» — нет ни в одном источнике (РБК Кубань, Интерфакс, Коммерсантъ, Профиль, поиск)
 dict(id='g6bf4b33c', field='eco.val', old='Долю оценивают в 15–17 млрд ₽, но не исключено, что сделка была безденежной.',
      new='—', quote='', url=''),
]
COMPANY = [
 ('ge6453621', 'desc', 'Девелопер, входит в топ-30 застройщиков РФ и топ-5 в Краснодарском крае; строит жилье и апартаменты в Краснодарском крае и Москве.',
  'Девелопер полного цикла из Краснодара, работает с 2007 года; по данным компании, входит в топ-5 застройщиков Краснодарского края и топ-20 в России по объему текущего строительства. Строит в Краснодарском крае, Москве и Подмосковье.'),
]

VED_GEN = 'https://www.vedomosti.ru/business/articles/2024/09/16/1062606-genotek-kupila'
REG_GEN = 'https://datanewton.ru/api/v2/history?ogrn=5177746308394&startDate=2017-01-01&attributes=OWNERS'
Q_REG_GEN = ('ЕГРЮЛ, участники ООО «Клиника Генотек Здоровье» (ИНН 7704448842, ОГРН 5177746308394), запись от 2024-09-13: '
             'вышли ООО "ЯНДЕКС" 99,9% и ООО "ГИС ТЕХНОЛОГИИ" 0,1%; вошло ООО "ГЕНОТЕК" (ОГРН 1117746016508) 100%.')
EDITS += [
 # g8ef19fd4 Genotek / «Яндекс.Здоровье»
 dict(id='g8ef19fd4', field='title', old='Яндекс продал телемедицинский сервис «Яндекс.Здоровье» компании Genotek',
      new='Genotek купил «Яндекс.Здоровье» у «Яндекса»',
      quote='Медицинская компания Genotek, специализирующаяся на генетических исследованиях, купила у IT-компании «Яндекс» телемедицинский сервис «Яндекс.Здоровье».', url=VED_GEN),
 dict(id='g8ef19fd4', field='date', old='2024-09-16', new='2024-09-13', quote=Q_REG_GEN, url=REG_GEN),
 dict(id='g8ef19fd4', field='src', old=[['Ведомости', VED_GEN]],
      new=[['Ведомости', VED_GEN], ['Sostav.ru', 'https://www.sostav.ru/publication/genotek-70103.html'],
           ['Expert.ru', 'https://expert.ru/tekhnologii/zdorove-stanet-chastyu-genotek']], quote='', url=''),
]
COMPANY += [
 ('ge6af02f6', 'legal_short', None, 'ООО «Генотек»'),
 ('g14239b0d', 'legal_short', None, 'ООО «Клиника Генотек Здоровье»'),
 ('g14239b0d', 'desc', 'Телемедицинский сервис, ранее принадлежавший Яндексу (ООО «КЛИНИКА ЯНДЕКС.ЗДОРОВЬЕ»); продан Genotek.',
  'Телемедицинский сервис: онлайн-консультации врачей и психологов. До сентября 2024 года принадлежал «Яндексу», теперь работает как Genotek Здоровье; консультации оказывает ООО «Клиника Генотек Здоровье».'),
]

RETRACT = []  # eco.val в retracted не пишется: enrich сверяет только sum, status и стороны

DP_MP = 'https://www.dp.ru/a/2024/09/18/dolja-reklamnogo-operatora'
REG_MP = 'https://datanewton.ru/api/v2/history?ogrn=1157847027854&startDate=2024-01-01&attributes=OWNERS'
Q_REG_MP = ('ЕГРЮЛ, участники ООО «Медиа Простор» (ИНН 7801271622, ОГРН 1157847027854), запись от 2024-09-11: '
            'вышло ООО "АБРИС" (ОГРН 1247800085081) 100%; вошло ООО "РУСС АУТДОР" (ОГРН 1037739331860, ИНН 7731196087) 100%.')
EDITS += [
 # g707633b2 Russ / «Медиа Простор»: покупатель и продавец — по ЕГРЮЛ
 dict(id='g707633b2', field='title', old='ГК Russ приобрела оператора наружной рекламы «Медиа Простор»',
      new='Russ Outdoor купил «Медиа Простор»',
      quote='Новым собственником 100% уставного капитала в размере 213,3 тыс. рублей стало ООО "Русс Аутдор", входящее в группу Russ.', url=DP_MP),
 dict(id='g707633b2', field='buyer', old='g549ab474', new='gbaa98e6b', quote=Q_REG_MP, url=REG_MP),
 dict(id='g707633b2', field='seller', old='Олег Петрович Зеваков', new='ООО «Абрис»', quote=Q_REG_MP, url=REG_MP),
 dict(id='g707633b2', field='eco.share', old='«Медиа Простор» управляет рекламой на 490 остановочных павильонах городского общественного транспорта Санкт-Петербурга. Сделка увеличила долю Russ на автобусных остановках города более чем до 80%.', new='100% доли в ООО «Медиа Простор»',
      quote='Новым собственником 100% уставного капитала в размере 213,3 тыс. рублей стало ООО "Русс Аутдор", входящее в группу Russ.', url=DP_MP),
 # TAdviser отдает 404 — мертвая ссылка; на ее месте ДП и AdIndex
 dict(id='g707633b2', field='src', old=[['Sostav.ru', 'https://www.sostav.ru/publication/gk-russ-priobrela-media-prostor-70142.html'], ['TAdviser', 'https://www.tadviser.ru/index.php/Компания:Russ_(Русс_Аутдор_ранее_Russ_Outdoor)']],
      new=[['Sostav.ru', 'https://www.sostav.ru/publication/gk-russ-priobrela-media-prostor-70142.html'], ['Деловой Петербург', DP_MP],
           ['AdIndex', 'https://adindex.ru/news/marketing/2024/09/18/325685.phtml']], quote='', url=''),
]
COMPANY += [
 ('gd68e5cf2', 'legal_short', None, 'ООО «Медиа Простор»'),
 ('gd68e5cf2', 'desc', 'Оператор наружной рекламы, приобретен ГК Russ.',
  'Петербургский оператор рекламы на остановках: по договору с городом 2019 года ставит и обслуживает около 490 остановочных павильонов. С сентября 2024 года принадлежит группе Russ.'),
]
RETRACT += [('g707633b2', 'seller', 'Олег Петрович Зеваков')]


CN_BR = 'https://www.cnews.ru/news/line/2024-09-11_hajv_investiruet_v_kompaniyu'
REG_BR = 'https://datanewton.ru/api/v2/history?ogrn=1187746690768&startDate=2024-09-01&attributes=OWNERS'
EDITS += [
 # g77b24b1c «Хайв» / Briskly: инвестиция через увеличение капитала, $1,7 млн — вложение трех инвесторов вместе
 dict(id='g77b24b1c', field='title', old='Фонд «Хайв» (ВымпелКом) купил долю в разработчике автономной торговли Briskly',
      new='«Хайв» купил 10,15% Briskly',
      quote='ООО «ХАЙВ» ( венчурный фонд , созданный компанией «ВымпелКом», соинвестором которого в 2024 г. стал « ТАГРАС ») приобрело долю 10,15% в ООО «Брискли» ( Briskly )', url=CN_BR),
 dict(id='g77b24b1c', field='eco.share', old='Через приложение Briskly B-Pay прошло свыше восьми млн покупок, примерно на 1,5 млрд ₽, а платформу используют свыше трех тыс. предпринимателей из России, Казахстана и Белоруссии. На счету компании больше 15 тыс. единиц умного оборудования. Среди него — микромаркеты: они заменяют прежние торговые автоматы и позволяют продавать свежие продукты.', new='10,15%',
      quote='приобрело долю 10,15% в ООО «Брискли» ( Briskly )', url=CN_BR),
 dict(id='g77b24b1c', field='sum_basis', old=None, new='raise', quote='', url=''),
 dict(id='g77b24b1c', field='date_basis', old=None, new='registry', quote='', url=''),
]
COMPANY += [
 ('g49f9a408', 'name', 'ООО «Бриски»', 'Briskly'),
 ('g49f9a408', 'legal_short', None, 'ООО «Брискли»'),
 ('g49f9a408', 'desc', 'Разработчик технологий автономной торговли (бренд Briskly, B-Pay); в 2024 году в него инвестировала «Хайв» (венчурный фонд «Билайна»), получив 10,15% долей за $1,7 млн.',
  'Разработчик технологий торговли без продавцов (приложение B-Pay, микромаркеты); собственный завод в Выборге. Основана в 2018 году.'),
 ('g1209e3c2', 'legal_short', None, 'ООО «Хайв»'),
]


MATCH += [('g49f9a408', 'briskly'), ('g49f9a408', 'брискли')]

K_RUB = 'https://www.kommersant.ru/doc/7030621'
EDITS += [
 # gd6ce73ed «Рубеж» / «Внуково 2»
 dict(id='gd6ce73ed', field='title', old='«Рубеж» выкупил площади в логистическом центре «Внуково 2»',
      new='«Рубеж» купил склад в логистическом центре «Внуково 2»',
      quote='О том, что «Рубеж» заключил сделку по покупке 12,5 тыс. кв. м в логистическом центре класса А «Внуково 2», рассказал источник “Ъ” на рынке.', url=K_RUB),
 # 10 сентября — день статьи «Коммерсанта», дня сделки в источниках нет
 dict(id='gd6ce73ed', field='date', old='2024-09-10', new='2024',
      quote='Коммерсантъ, 10.09.2024: «Рубеж» выкупил большой объем площадей в логистическом центре «Внуково 2» — день сделки в статье не назван, это день публикации.', url=K_RUB),
 dict(id='gd6ce73ed', field='sum_basis', old=None, new='estimate', quote='', url=''),
 dict(id='gd6ce73ed', field='src', old=[['Retail.ru', 'https://www.retail.ru/news/-rubezh-vykupil-za-1-mlrd-rub-bolshoy-obem-ploshchadey-v-logisticheskom-tsentre--10-sentyabrya-2024-244759/'], ['Коммерсантъ', 'https://www.kommersant.ru/doc/7030621']],
      new=[['Коммерсантъ', K_RUB], ['Retail.ru', 'https://www.retail.ru/news/-rubezh-vykupil-za-1-mlrd-rub-bolshoy-obem-ploshchadey-v-logisticheskom-tsentre--10-sentyabrya-2024-244759/']], quote='', url=''),
 dict(id='gd6ce73ed', field='accepted_notes', old=None,
      new={'no_profile': {'seller': 'Продавец площадей не назван: Коммерсантъ (стороны на запрос не ответили), Retail.ru (пересказ Ъ), поиск «Рубеж» + «Внуково 2» + 12,5 тыс. кв. м, поиск собственника и девелопера ЛЦ «Внуково 2», поиск сообщений консультантов Bright Rich | CORFAC International и «Ricci | Склады»; помещение — не ООО, реестр участников не поможет (12 ноября 2026, вычитка m028).'}},
      quote='', url=''),
]
COMPANY += [
 ('gb68d459f', 'name', 'складские площади в логистическом центре «Внуково 2»', 'Склад в логистическом центре «Внуково 2»'),
 ('gb68d459f', 'desc', 'Складские площади рядом с аэропортом Внуково; в 2024 году их купил производитель систем безопасности «Рубеж».',
  '12,5 тыс. кв. м складских помещений в логистическом центре класса А «Внуково 2» у аэропорта Внуково; в 2024 году их купил производитель систем безопасности «Рубеж».'),
]

MATCH += [('gb68d459f', 'склад в логистическом центре внуково 2')]

IF_PGK = 'https://www.interfax.ru/business/979610'
AKM_PGK = 'https://www.akm.ru/news/vtb_prodal_kompaniyu_avrora_invest/'
RBC_PGK = 'https://www.rbc.ru/business/05/09/2024/66d95b939a7947a0f9b25fd6'
Q_AKM_PGK = ('Банк ВТБ вышел из капитала АО «Аврора Инвест», владеющей Первой грузовой компанией: 100% компании, которая '
             'изначально рассматривалась как инвестиционный актив, продано с хорошей прибылью для банка. … В ноябре 2023 г. '
             'ПГК у структур владельца НЛМК Владимира Лисина выкупило АО "Аврора Инвест". Собственники последнего не раскрываются.')
EDITS += [
 # gb101d54d ВТБ / ПГК: ВТБ получил ПГК вместе с АО «Аврора Инвест» — «Аврора» не продавец, а купленная компания;
 # кто владел ею до банка, не раскрыто. Сумма «Более 200 млрд ₽ (с учетом долга)» оставлена: золотая выборка
 # (pipeline/gold/analytics_gold.json) читает ее как нижнюю границу.
 dict(id='gb101d54d', field='title', old='ВТБ приобрел Первую грузовую компанию', new='ВТБ купил Первую грузовую компанию',
      quote='ВТБ купил Первую грузовую компанию исходя из оценки более 200 млрд руб. с учетом долга, сообщил Андрей Костин', url=RBC_PGK),
 dict(id='gb101d54d', field='seller_id', old='gb1ea6ff5', new=None, quote=Q_AKM_PGK, url=AKM_PGK),
 dict(id='gb101d54d', field='seller', old='АО «Аврора Инвест»', new=None, quote=Q_AKM_PGK, url=AKM_PGK),
 # дня закрытия в источниках нет: 5 сентября 2024 года Костин сообщил, что сделка уже состоялась
 dict(id='gb101d54d', field='date_basis', old=None, new='announcement', quote='', url=''),
 dict(id='gb101d54d', field='accepted_notes', old=None,
      new={'no_profile': {'seller': 'ВТБ получил ПГК вместе с ее владельцем АО «Аврора Инвест» (в декабре 2024 года банк продал 100% «Аврора Инвест»), значит продавцы — прежние акционеры «Аврора Инвест». Они не раскрыты: Интерфакс («собственники не раскрываются»; по данным источников — группа инвесторов с Тимуром и Русланом Бабаевыми), РБК, AK&M, Интерфакс 29.04.2025; реестр акционеров АО не показывает (12 ноября 2026, вычитка m028).'}},
      quote='', url=''),
]
COMPANY += [
 ('gdd278a7f', 'legal_short', None, 'АО «ПГК»'),
 ('gb1ea6ff5', 'desc', 'Московская холдинговая компания; до 2024 года владела оператором грузовых вагонов ПГК. Юрлицо — АО «Аврора Инвест».',
  'Московская холдинговая компания, с ноября 2023 года владелец оператора грузовых вагонов ПГК. В 2024 году 100% компании принадлежали ВТБ; в декабре 2024 года банк их продал, покупатель не раскрыт. Юрлицо — АО «Аврора Инвест».'),
]
RETRACT += [('gb101d54d', 'seller', 'АО «Аврора Инвест»')]


IF_IRE = 'https://www.interfax.ru/business/1018117'
SL_IRE = 'https://softline.ru/about/news/gk-softline-priobretaet-kontroliruyushchuyu-dolyu-v-nto-ire-polyus-i-rasshiryaet-svoy-nauchno-tekhnologicheskij-potencial-na-mezhdunarodnom-urovne'
IPG_IRE = 'https://investor.ipgphotonics.com/news/news-details/2024/IPG-Photonics-Announces-Sale-of-its-Russian-Operations/default.aspx'
Q_SUM_IRE = 'Сумма самой сделки, о которой было объявлено в сентябре 2024 года, составила 4,58 млрд рублей.'
EDITS += [
 # g00773994 Softline / «ИРЭ-Полюс»: сумма по отчету Softline (в релизе было «порядка 4,5 млрд»), доля — 100% через «БВПГ»
 dict(id='g00773994', field='title', old='Softline приобрела контроль в производителе лазеров ИРЭ-Полюс у IPG Photonics',
      new='Softline купил «ИРЭ-Полюс» у IPG Photonics',
      quote='объявляет о приобретении контролирующей доли в НТО «ИРЭ-Полюс» у международной группы IPG Photonics, базирующейся в США', url=SL_IRE),
 dict(id='g00773994', field='sum', old='4,5 млрд ₽', new='4,58 млрд ₽', quote=Q_SUM_IRE, url=IF_IRE),
 dict(id='g00773994', field='eco.sum', old='4,5 млрд ₽', new='4,58 млрд ₽', quote=Q_SUM_IRE, url=IF_IRE),
 dict(id='g00773994', field='eco.share', old='Доли «ИРЭ-Полюса» в России: около 90% выпуска волоконных лазеров, около 70% рынка промышленных лазеров, в медицине — 80% урологии и 40% флебологии и хирургических лазеров.', new='100% доли в ООО «НТО «ИРЭ-Полюс»»',
      quote='Еще в сентябре 2024 г. вместо иностранных владельцев - IPG Photonics Corporation (США) и IPG Laser GmbH & Co. KG (Германия) единственным собственником "ИРЭ-Полюс" стало ООО "БВПГ"',
      url='https://www.comnews.ru/content/238253/2025-03-14/2025-w11/1008/ire-polyus-zasvetilsya-kak-vpg-laserone'),
 dict(id='g00773994', field='src', old=[['Softline.ru', 'https://softline.ru/about/news/gk-softline-priobretaet-kontroliruyushchuyu-dolyu-v-nto-ire-polyus-i-rasshiryaet-svoy-nauchno-tekhnologicheskij-potencial-na-mezhdunarodnom-urovne'], ['Softline.ru', 'https://softline.ru/about/news/gk-softline-obyavlyaet-o-smene-nazvaniya-kompanii-nto-ire-polyus-na-vpg-laserone-s-7-marta-2025-goda'], ['ComNews', 'https://www.comnews.ru/content/238253/2025-03-14/2025-w11/1008/ire-polyus-zasvetilsya-kak-vpg-laserone'], ['Интерфакс', 'https://www.interfax.ru/business/1018117']],
      new=[['Softline.ru', 'https://softline.ru/about/news/gk-softline-priobretaet-kontroliruyushchuyu-dolyu-v-nto-ire-polyus-i-rasshiryaet-svoy-nauchno-tekhnologicheskij-potencial-na-mezhdunarodnom-urovne'], ['Softline.ru', 'https://softline.ru/about/news/gk-softline-obyavlyaet-o-smene-nazvaniya-kompanii-nto-ire-polyus-na-vpg-laserone-s-7-marta-2025-goda'], ['ComNews', 'https://www.comnews.ru/content/238253/2025-03-14/2025-w11/1008/ire-polyus-zasvetilsya-kak-vpg-laserone'], ['Интерфакс', 'https://www.interfax.ru/business/1018117']] + [['IPG Photonics', IPG_IRE]], quote='', url=''),
]
COMPANY += [
 ('g71078e21', 'name', 'ООО «ИРЭ-Полюс»', 'ИРЭ-Полюс'),
 ('g71078e21', 'legal_short', None, 'ООО «ВПГ Лазеруан»'),
 ('g71078e21', 'desc', 'Российский производитель промышленных лазеров.',
  'Крупнейший в России производитель волоконных лазеров (промышленные и медицинские лазеры, телеком-оборудование), Фрязино. Основан Валентином Гапонцевым в 1991 году, был базой группы IPG Photonics; с сентября 2024 года принадлежит ООО «БВПГ» (60% — Softline), с марта 2025 года называется VPG LaserONE (ООО «ВПГ Лазеруан»).'),
]
MATCH += [('g71078e21', 'ирэ-полюс'), ('g71078e21', 'vpg laserone'), ('g71078e21', 'впг лазеруан')]


IF_ROLF = 'https://www.interfax.ru/business/1000901'
Q_ROLF = ('В августе 2024 года АО "Автомобильные технологии" приобрело у Федерального агентства по управлению государственным '
          'имуществом (Росимущество) АО "Рольф", ООО "Рольф Моторс", ООО "Рольф Эстейт Санкт-Петербург",')
EDITS += [
 # g69a22dab «Рольф»: покупатель по отчетности — АО «Автомобильные технологии» (99% у АО «ПромАгроЛогистика»),
 # Кремлев — конечный бенефициар; ему место в прозе, а не в схеме (docs/card_parties.md, 11 ноября 2026)
 dict(id='g69a22dab', field='title', old='Структура Умара Кремлева приобрела «Рольф» у Росимущества',
      new='«Автомобильные технологии» купили «Рольф» у Росимущества', quote=Q_ROLF, url=IF_ROLF),
 dict(id='g69a22dab', field='buyer', old='g6f5d7e99', new='g47e035e6', quote=Q_ROLF, url=IF_ROLF),
 # расчет «EBITDA × 3 = 40,3 млрд ₽» и «около 30 млрд ₽ с долгом» не нашлись ни в одном источнике; цена известна (34,798 млрд ₽)
 dict(id='g69a22dab', field='eco.val', old='Расчетная оценка сделки — около 40,3 млрд ₽: столько выходит, если взять скорректированную EBITDA «Рольфа» за 2023 год и умножить на три. По неофициальным данным, в три годовые EBITDA обычно и оценивают дилерский бизнес. По другим неофициальным данным, «Рольф» с учетом долга мог стоить около 30 млрд ₽.', new='—', quote='', url=''),
]
COMPANY += [
 ('g47e035e6', 'name', None, 'Автомобильные технологии'),
 ('g47e035e6', 'legal_short', None, 'АО «Автомобильные технологии»'),
 ('g47e035e6', 'ind', None, 'Автопром'),
 ('g47e035e6', 'kpi', None, ['Профиль']),
 ('g47e035e6', 'desc', None,
  'Акционерное общество, учреждено в мае 2024 года; с августа 2024 года 99% у АО «ПромАгроЛогистика», головной компании группы «Рольф». В августе 2024 года купило у Росимущества АО «Рольф» и другие компании группы. Конечный бенефициар, по сообщениям компании, — Умар Кремлев.'),
]
MATCH += [('g47e035e6', 'автомобильные технологии'), ('g47e035e6', 'ао «автомобильные технологии»'), ('g47e035e6', 'ао автомобильные технологии')]





def get(card, field):
    if '.' in field:
        head, tail = field.split('.', 1)
        return (card.get(head) or {}).get(tail)
    return card.get(field)


def put(card, field, value):
    if '.' in field:
        head, tail = field.split('.', 1)
        card.setdefault(head, {})[tail] = value
    elif value is None:
        card.pop(field, None)
    else:
        card[field] = value


def apply(data, verbose=False):
    by = {d['id']: d for d in data['deals']}
    done = skipped = 0
    for e in EDITS:
        card = by[e['id']]
        cur = get(card, e['field'])
        if cur == e['new']:
            skipped += 1
            continue
        assert cur == e['old'], '%s %s: в базе %r, ожидали %r' % (e['id'], e['field'], cur, e['old'])
        put(card, e['field'], e['new'])
        if e['field'] in FACT:
            fact_edit_guard.log(card, e['field'], e['new'], e['quote'], e['url'], BY, DAY)
        done += 1
        if verbose:
            print('%s %s: %r → %r' % (e['id'], e['field'], str(cur)[:80], str(e['new'])[:80]))
    for cid, key, old, new in COMPANY:
        comp = data['companies'].setdefault(cid, {}) if old is None else data['companies'][cid]
        if comp.get(key) == new:
            skipped += 1
            continue
        assert comp.get(key) == old, '%s.%s: %r' % (cid, key, comp.get(key))
        if new is None:
            comp.pop(key, None)
        else:
            comp[key] = new
        done += 1
        if verbose:
            print('профиль %s.%s: %r → %r' % (cid, key, str(old)[:80], str(new)[:80]))
    for cid, key in MATCH:
        keys = data.setdefault('match_keys', {}).setdefault(cid, [])
        if key not in keys:
            keys.append(key)
            done += 1
    for did, field, value in RETRACT:
        lst = by[did].setdefault('retracted', {}).setdefault(field, [])
        if value not in lst:
            lst.append(value)
    return done, skipped


def main(write):
    raw = open(DATA, encoding='utf-8').read()
    old, data = json.loads(raw), json.loads(raw)
    done, skipped = apply(data, verbose=True)
    print('правок: %d, уже применено: %d' % (done, skipped))
    mass_edit_guard.check(old, data, os.environ.get('MASS_OK'))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    if not done:
        print('Все уже применено.')
        rebaseline(json.loads(raw))
        return 0
    fresh_raw = open(DATA, encoding='utf-8').read()
    fresh = json.loads(fresh_raw)
    apply(fresh)
    with open(DATA, 'w', encoding='utf-8') as f:
        f.write(json.dumps(fresh, ensure_ascii=False, indent=1) + ('\n' if fresh_raw.endswith('\n') else ''))
    print('ЗАПИСАНО.')
    rebaseline(fresh)
    return 0


def rebaseline(data):
    """Исправленные вычиткой старые нарушения правил текста уходят из text_rules_baseline.json
    (test_card_text_follows_the_house_rules требует убрать «исправленные»). Только для карточек
    партии и только сокращение списка."""
    import text_rules
    ids = {e['id'] for e in EDITS}
    known = json.load(open(text_rules.BASELINE, encoding='utf-8'))
    now = {f[0] for f in text_rules.all_findings({'deals': [d for d in data['deals'] if d['id'] in ids]})}
    left = [fp for fp in known['known'] if fp.split('|')[0] not in ids or fp in now]
    if len(left) != len(known['known']):
        print('из списка старых нарушений убрано: %d' % (len(known['known']) - len(left)))
        known['known'] = left
        with open(text_rules.BASELINE, 'w', encoding='utf-8') as fh:
            json.dump(known, fh, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv[1:]))
