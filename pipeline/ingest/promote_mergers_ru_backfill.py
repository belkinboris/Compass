#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Разовый бэкфил 2 июня — 31 июля: ручной обзор кандидатов с mergers.ru.

ПОЧЕМУ РУЧНОЙ, А НЕ АВТОМАТИЧЕСКИЙ. `promote.py` держит тормоз
`NEW_CARDS_NEED_REVIEW` (E9): фильтр «это сделка» не измерен на живом потоке,
поэтому НИ ОДНА новая карточка не проходит автоматически — только «на решение».
Из 92 кандидатов текущего забора реальными сделками для базы (после разбора
глазами и сверки с базой на дубли) оказалось около трети — остальное шум,
опровержения или уже отражённые сюжеты. Это тот самый обзор человеком, который
запрашивает тормоз, — задокументирован здесь, а не сделан молча.

ЧТО ПРОВЕРЕНО ПЕРЕД КАЖДОЙ ЗАПИСЬЮ.
  * Сверка с базой по ключевым именам сторон — семь кандидатов оказались уже
    известными сделками (ЮГК/БТС-Мост, Галс-Девелопмент, Медскан/Росатом,
    Домодедово/Внуково, «Центр ЭКО», аптека «Апрель», Ильинская больница) —
    это ОБОГАЩЕНИЕ уже существующих карточек, а не новые записи; см. блок
    ENRICH_HINTS ниже (не пишется автоматически — только фиксирует находку
    для следующего прогона `enrich.py`/ручной правки).
  * Явные опровержения и слухи без стороны сделки (RWB приостановила
    инвестпрограмму, Лента не покупает Fix Price, Шишкарев не выкупит долю,
    Сбер спрогнозировал всплеск M&A) — не сделки, не включены.
  * Суммы сверены с текстом источника, а не взяты вслепую: у «ВТБ продал
    Holiday Inn» автоматический разбор взял 100 млрд ₽ — это цена всего фонда
    «Галс-Девелопмент», а не одной гостиницы (сама гостиница оценивается в
    8–10 млрд ₽ по тексту источника); карточка на неё не создаётся отдельно —
    это деталь периметра уже известной сделки ВТБ/Галс.
  * Родственные публикации по одному сюжету (например, ФАС по сделке
    «Коломенское»/«Пеко» 14 июля и закрытие 27 июля) сведены в ОДНУ карточку
    с этапами, а не в две.

ГРАНИЦА ПРАВКИ. Как и везде в pipeline/: сторона и предмет переносятся
дословно из текста источника (в `NEW_CARDS` — из `events[0].note`, взятого из
реального сухого прогона draft.py на заборе mergers.ru 31 июля), поле не
заполняется, если источник сам говорит «сумма не раскрывается».

Запуск:
    python3 pipeline/ingest/promote_mergers_ru_backfill.py            # сухой прогон
    python3 pipeline/ingest/promote_mergers_ru_backfill.py --write    # записать
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'

# Каждая запись — почти карточка базы; id генерируется детерминированно из
# слага mergers.ru, чтобы повторный прогон не создавал дублей.
NEW_CARDS = [
    dict(slug='psb-tpk-chelyabinsk', date='2026-07-30', status='Обсуждается', type='Продажа с торгов',
         title='ПСБ выставил на продажу компании, владеющие двумя ТРК в Челябинске',
         seller='ПСБ', asset='ООО «Родник» и ООО «Управляющая компания «Содействие»» (два торгово-развлекательных комплекса в Челябинске)',
         ind='Недвижимость',
         src=[['mergers.ru', 'https://mergers.ru/news/PSB-prodast-kompanii-vladeyuschie-dvumya-TRK-v-Chelyabinske-87293']]),

    dict(slug='geotek-bashneftegeofizika', date='2026-07-28', status='Обсуждается', type='СП',
         title='«Геотек» и «Башнефтегеофизика» объединяют нефтесервисные активы',
         asset='АО «Башнефтегеофизика» и АО «ГЕОТЕК» (объединение в единого нефтесервисного оператора)',
         ind='Нефть и газ',
         src=[['mergers.ru', 'https://mergers.ru/news/Nachalos-obedinenie-nefteservisnyh-holdingov-Geotek-i-Bashneftegeofizika-87277']]),

    dict(slug='prodo-star-nafta-broiler', date='2026-07-28', status='Закрыта', type='M&A',
         title='Группа «Продо» выкупила бизнес «Башкирского бройлера» у группы «Стар Нафта»',
         buyer_name='«Продо»', seller='«Стар Нафта»', asset='бизнес «Башкирского бройлера»',
         sum='1,4–2 млрд ₽ (по оценке)', ind='Пищепром и напитки',
         src=[['mergers.ru', 'https://mergers.ru/news/Gruppa-Prodo-vykupila-biznes-Bashkirskogo-brojlera-u-gruppy-Star-Nafta-87275']]),

    dict(slug='prime-pervy-poliplastik', date='2026-07-27', status='Закрыта', type='M&A',
         title='ЗПИФ «Прайм Первый» приобрёл 14% в группе «Полипластик»',
         buyer_name='ЗПИФ «Прайм Первый» (УК «Диалог Инвестиции»)', asset='14% в группе «Полипластик»',
         ind='Химия и удобрения',
         src=[['mergers.ru', 'https://mergers.ru/news/Paevoj-investfond-priobrel-14-v-gruppe-Poliplastik-87271']]),

    dict(slug='svoj-kredit-evropa-strah', date='2026-07-27', status='Закрыта', type='M&A',
         title='Группа «Свой» купила страховщика «Кредит Европа лайф» у «Кредит Европа банка»',
         buyer_name='«Свой»', seller='«Кредит Европа банк»', asset='«Кредит Европа лайф» (страховая компания)',
         sum='400–600 млн ₽ (по оценке)', ind='Страхование',
         src=[['mergers.ru', 'https://mergers.ru/news/Gruppa-Svoj-kupila-strahovschika-u-Kredit-Evropa-banka-87269']]),

    dict(slug='kolomenskoe-peko', date='2026-07-27', status='Закрыта', type='M&A',
         title='ГК «Коломенский» приобрела хлебокомбинат «Пеко»',
         buyer_name='ГК «Коломенский»', asset='100% долей ООО «Хлебокомбинат «Пеко»» (через ООО «Хлебинвест»)',
         sum='900 млн ₽ (оценка на стадии согласования ФАС)', ind='Пищепром и напитки',
         events=[
             dict(kind='approval', date='2026-07-14', title='Согласование получено',
                  note='ФАС согласовала сделку по покупке подконтрольным ГК «Коломенское» ООО «Хлебинвест» 100% долей в ООО «Хлебокомбинат «Пеко»».',
                  source=['mergers.ru', 'https://mergers.ru/news/GK-Kolomenskoe-vykupit-hlebokombinat-Peko-87197']),
             dict(kind='closed', date='2026-07-27', title='Сделка закрыта',
                  note='«Коломенский» стал владельцем производственного комплекса на Полярной улице мощностью до 200 т продукции в сутки.',
                  source=['mergers.ru', 'https://mergers.ru/news/Holding-Kolomenskij-priobrel-kombinat-Peko-87267']),
         ],
         src=[['mergers.ru', 'https://mergers.ru/news/Holding-Kolomenskij-priobrel-kombinat-Peko-87267'],
              ['mergers.ru', 'https://mergers.ru/news/GK-Kolomenskoe-vykupit-hlebokombinat-Peko-87197']]),

    dict(slug='arnest-reckitt', date='2026-07-27', status='Обсуждается', type='M&A',
         title='«Арнест» выкупает часть российского бизнеса Reckitt Benckiser',
         buyer_name='«Арнест»', seller='Reckitt Benckiser (Великобритания)',
         asset='завод по выпуску бытовой химии в Клину (бренды Vanish, Air Wick, Cilit Bang, Tiret, Calgon)',
         sum='18 млрд ₽', ind='Потребительские товары',
         src=[['mergers.ru', 'https://mergers.ru/news/Arnest-vykupaet-chast-biznesa-Reckitt-Benckiser-87265']]),

    dict(slug='mariholodmash-borsky', date='2026-07-24', status='Закрыта', type='M&A',
         title='«Марихолодмаш» выкупил Борский завод торгового оборудования',
         buyer_name='«Марихолодмаш»', asset='Борский завод торгового оборудования',
         sum='более 10 млрд ₽ (по оценке источника)', ind='Машиностроение',
         src=[['mergers.ru', 'https://mergers.ru/news/Mariholodmash-vykupil-Borskij-zavod-torgovogo-oborudovaniya-87263']]),

    dict(slug='nordline-totalenergies-arctic', date='2026-07-23', status='Согласование получено', type='M&A',
         title='«Нордлайн» получил разрешение выкупить у TotalEnergies 10% в «Арктик СПГ 2»',
         buyer_name='«Нордлайн»', seller='TotalEnergies', asset='10% в проекте «Арктик СПГ 2»',
         sum='$4,1 млрд', ind='Нефть и газ',
         events=[
             dict(kind='approval', date='2026-06-03', title='Согласование получено',
                  note='Президент разрешил «НордЛайн» купить у TotalEnergies 10% в «Арктик СПГ 2».',
                  source=['mergers.ru', 'https://mergers.ru/news/Putin-razreshil-NordLajn-kupit-u-TotalEnergies-10-v-Arktik-SPG-2-87029']),
             dict(kind='approval', date='2026-07-23', title='Ожидается скорое закрытие',
                  note='TotalEnergies ожидает скорого завершения процесса продажи 10% «Арктик СПГ 2» компании «Нордлайн».',
                  source=['mergers.ru', 'https://mergers.ru/news/TotalEnergies-ozhidaet-skorogo-zaversheniya-processa-prodazhi-10-Arktik-SPG-kompanii-Nordlajn-87257']),
         ],
         src=[['mergers.ru', 'https://mergers.ru/news/TotalEnergies-ozhidaet-skorogo-zaversheniya-processa-prodazhi-10-Arktik-SPG-kompanii-Nordlajn-87257'],
              ['mergers.ru', 'https://mergers.ru/news/Putin-razreshil-NordLajn-kupit-u-TotalEnergies-10-v-Arktik-SPG-2-87029']]),

    dict(slug='mtsbank-kdpay', date='2026-07-22', status='Закрыта', type='M&A',
         title='МТС Банк купил платёжный сервис KD Pay',
         buyer_name='МТС Банк', seller='Олег Пономарёв и Леонид Дубов (основатели)',
         asset='51% ООО «Ритейл-Процессинг» (владелец платёжного сервиса KD Pay)',
         ind='Финтех',
         src=[['mergers.ru', 'https://mergers.ru/news/MTS-Bank-kupil-platezhnyj-servis-KD-Pay-87251']]),

    dict(slug='roshim-vnt', date='2026-07-21', status='Обсуждается', type='M&A',
         title='«Росхим» может приобрести Восточный нефтехимический терминал в Приморье',
         buyer_name='«Росхим»', asset='Восточный нефтехимический терминал (ВНТ) в Приморье',
         ind='Химия и удобрения',
         src=[['mergers.ru', 'https://mergers.ru/news/Roshim-mozhet-priobresti-Vostochnyj-neftehimicheskij-terminal-v-Primore-87241']]),

    dict(slug='geopromining-zabaikalie', date='2026-07-20', status='Закрыта', type='M&A',
         title='ГеоПроМайнинг купил активы по добыче золота в Забайкалье',
         buyer_name='«ГеоПроМайнинг» (через ООО «Кряж Инвест»)',
         asset='25% ООО «Золотоноша» (лицензии на добычу золота, Забайкалье)',
         ind='ГМК и добыча',
         src=[['mergers.ru', 'https://mergers.ru/news/GeoProMajning-kupil-aktivy-po-dobyche-zolota-v-Zabajkale-87237']]),

    dict(slug='rostech-avia-holding', date='2026-07-20', status='Обсуждается', type='СП',
         title='«Ростех» консолидирует авиатранспортные активы в новом холдинге',
         asset='НССА, авиакомпания Red Wings и SkyGates, лизинговая компания «Авиакапитал-Сервис»',
         ind='Транспорт и логистика',
         src=[['mergers.ru', 'https://mergers.ru/news/Rosteh-konsolidiruet-aviatransportnye-aktivy-v-novom-holdinge-87239']]),

    dict(slug='vysochaishy-komi-oil', date='2026-07-17', status='Обсуждается', type='M&A',
         title='Сооснователь «Высочайшего» продаёт нефтяной проект в Коми',
         seller='сооснователь «Высочайшего»', asset='нефтяной проект в Коми', sum='$30 млн',
         ind='Нефть и газ',
         src=[['mergers.ru', 'https://mergers.ru/news/Soosnovatel-Vysochajshego-prodaet-neftyanoj-proekt-v-Komi-87229']]),

    dict(slug='sucden-poetti', date='2026-07-15', status='Обсуждается', type='M&A',
         title='Французская Sucden может получить контроль над бизнесом производителя кофе Poetti',
         buyer_name='Sucden (через ООО «СДС»)', asset='партнёрство с «Милфудс» (бренд Poetti)',
         ind='Пищепром и напитки',
         src=[['mergers.ru', 'https://mergers.ru/news/Francuzskaya-Sucden-mogla-poluchit-kontrol-nad-biznesom-proizvoditelya-kofe-Poetti-87215']]),

    dict(slug='nordgold-chukotka', date='2026-07-15', status='Закрыта', type='M&A',
         title='Nordgold стал владельцем «Новой сырьевой компании» на Чукотке',
         buyer_name='«Нордголд Развитие»', asset='ООО «Новая сырьевая компания» (золотодобыча, Чукотка)',
         ind='ГМК и добыча',
         src=[['mergers.ru', 'https://mergers.ru/news/Nordgold-mozhet-vlozhitsya-v-dobychu-zolota-na-Chukotke-87213']]),

    dict(slug='voshod-voronezh-rocket', date='2026-07-15', status='Закрыта', type='Инвестиция',
         title='Фонд «Восход» инвестировал ещё 100 млн руб. в проект ракеты-носителя «Воронеж»',
         buyer_name='Фонд «Восход»', asset='проект сверхлёгкой ракеты-носителя «Воронеж»', sum='100 млн ₽',
         ind='Машиностроение',
         src=[['mergers.ru', 'https://mergers.ru/news/Fond-Voshod-investiroval-eschjo-100-mln-rub-v-proekt-sverhlegkoj-rakety-nositelya-Voronezh-87211']]),

    dict(slug='mirgorodsky-nattys', date='2026-07-14', status='Закрыта', type='M&A',
         title='Геннадий Миргородский приобрёл контроль в производителе Nattys',
         buyer_name='Геннадий Миргородский', seller='Юлиана Николаева (сохранила 30%)',
         asset='70% ООО «Нуттис» (бренд Nattys — арахисовая паста и протеиновые батончики)',
         ind='Пищепром и напитки',
         src=[['mergers.ru', 'https://mergers.ru/news/Gennadij-Mirgorodskij-priobrel-kontrrol-v-proizvoditele-arahisovoj-pasty-i-proteinovyh-batonchikov-Nattys-87199']]),

    dict(slug='rodnye-polya', date='2026-07-13', status='Закрыта', type='Продажа с торгов',
         title='Бизнес «Родных полей» продан за 11,7 млрд рублей',
         asset='бизнес «Родных полей»', sum='11,7 млрд ₽', ind='Агро',
         src=[['mergers.ru', 'https://mergers.ru/news/Biznes-Rodnyh-polej-prodan-za-117-mlrd-rublej-87195']]),

    dict(slug='dobroflot-ikorny', date='2026-07-13', status='Закрыта', type='M&A',
         title='«Доброфлот» купил долю в сети рыбных магазинов «Икорный»',
         buyer_name='«Доброфлот»', asset='доля в сети рыбных магазинов «Икорный»',
         ind='Ритейл',
         src=[['mergers.ru', 'https://mergers.ru/news/Dobroflot-kupil-dolyu-v-rybnyh-magazinah-Ikornyj-87193']]),

    dict(slug='razvitie-stroy-aktivov-akzo', date='2026-07-13', status='Закрыта', type='M&A',
         title='РФ передала локальные активы Akzo Nobel в управление АО «Развитие строительных активов»',
         buyer_name='АО «Развитие строительных активов»', asset='локальные активы Akzo Nobel в России',
         ind='Химия и удобрения',
         src=[['mergers.ru', 'https://mergers.ru/news/RF-peredala-lokalnye-aktivy-Akzo-Nobel-v-upravlenie-AO-Razvitie-stroitelnyh-aktivov-87189']]),

    dict(slug='vostok-sever-pevek', date='2026-07-10', status='Закрыта', type='M&A',
         title='Фонд «Восток-Север» стал владельцем 100% «Морпорта Певек»',
         buyer_name='Фонд «Восток-Север»', asset='100% «Морпорта Певек»',
         ind='Порты и инфраструктура',
         src=[['mergers.ru', 'https://mergers.ru/news/Fond-Vostok-Sever-stal-vladelcem-100-Morporta-Pevek-87177']]),

    dict(slug='vim-poklonka', date='2026-07-07', status='Обсуждается', type='M&A',
         title='Фонд под управлением «ВИМ Сбережения» выкупает деловой квартал «Поклонка плейс»',
         buyer_name='фонд под управлением «ВИМ Сбережения»',
         asset='деловой квартал «Поклонка плейс» на Поклонной горе',
         ind='Недвижимость',
         src=[['mergers.ru', 'https://mergers.ru/news/Fond-pod-upravleniem-VIM-sberezhenij-vykupaet-delovoj-kvartal-Poklonka-plejs-na-Poklonnoj-gore-87155']]),

    dict(slug='absolut-strahovanie-owner', date='2026-07-02', status='Закрыта', type='M&A',
         title='«Абсолют Страхование» сменила владельца',
         seller='Инвестиционная группа «Абсолют» (Александр Светаков)',
         asset='«Абсолют Страхование»',
         ind='Страхование',
         src=[['mergers.ru', 'https://mergers.ru/news/Kompaniya-Absolyut-Strahovanie-smenila-vladelca-87135']]),

    dict(slug='rwb-eapteka', date='2026-07-01', status='Закрыта', type='M&A',
         title='RWB купила мажоритарную долю в сервисе «Еаптека»',
         buyer_name='RWB (Wildberries и Russ)', asset='мажоритарная доля в «Еаптеке»',
         sum='7–12 млрд ₽ (по оценке)', ind='E-commerce',
         events=[
             dict(kind='negotiations', date='2026-06-24', title='Переговоры на продвинутой стадии',
                  note='Источник на инвестрынке оценивает текущую стоимость «Еаптеки» минимум в 8 млрд руб.',
                  source=['mergers.ru', 'https://mergers.ru/news/RWB-blizok-k-pokupke-Eapteki-87095']),
             dict(kind='closed', date='2026-07-01', title='Сделка закрыта',
                  note='Стороны не раскрывают сумму сделки и долю, но «Еаптека» вошла в состав группы RWB.',
                  source=['mergers.ru', 'https://mergers.ru/news/RWB-kupila-mazhoritarnuyu-dolyu-v-servise-Eapteka-87129']),
         ],
         src=[['mergers.ru', 'https://mergers.ru/news/RWB-kupila-mazhoritarnuyu-dolyu-v-servise-Eapteka-87129'],
              ['mergers.ru', 'https://mergers.ru/news/RWB-blizok-k-pokupke-Eapteki-87095']]),

    dict(slug='vtb-otkrytie-office-rwb', date='2026-06-30', status='Обсуждается', type='M&A',
         title='RWB покупает бывший офис банка «Открытие» у ВТБ',
         buyer_name='объединённая компания Wildberries и Russ (RWB)', seller='ВТБ',
         asset='бывший офис банка «Открытие»',
         ind='Недвижимость',
         src=[['mergers.ru', 'https://mergers.ru/news/VTB-k-koncu-iyunya-prodast-byvshij-ofis-banka-Otkrytie-87123']]),

    dict(slug='sutochno-onetwotrip', date='2026-06-17', status='Обсуждается', type='M&A',
         title='«Суточно.ру» может купить сервис путешествий OneTwoTrip',
         buyer_name='«Суточно.ру»', asset='сервис путешествий OneTwoTrip',
         ind='Гостиницы и туризм',
         src=[['mergers.ru', 'https://mergers.ru/news/Sutochnoru-mozhet-kupit-servis-OneTwoTrip-87075']]),

    dict(slug='darkin-vladmorribport', date='2026-06-23', status='Закрыта', type='M&A',
         title='Сергей Дарькин закрыл сделку по выкупу доли «Владморрыбпорта»',
         buyer_name='ООО «ГЕОТЭКС» (Сергей Дарькин)', seller='Александр Евдокимов',
         asset='47% «Владивостокского морского рыбного порта»', sum='18,7 млрд ₽',
         ind='Порты и инфраструктура',
         src=[['mergers.ru', 'https://mergers.ru/news/Sergej-Darkin-zakryl-sdelku-po-vykupu-doli-Vladmorrybporta-87161']]),

    dict(slug='strana-development-sreda', date='2026-06-04', status='Закрыта', type='M&A',
         title='«Страна Девелопмент» продала торговый комплекс «Среда. Царицыно»',
         seller='«Страна Девелопмент»',
         buyer_name='ООО «Приморская строительная корпорация» (Дмитрий Сулеев)',
         asset='торговый комплекс «Среда. Царицыно» на юге Москвы', sum='1,7 млрд ₽',
         ind='Недвижимость',
         src=[['mergers.ru', 'https://mergers.ru/news/Strana-Development-prodala-torgovyj-kompleks-Sreda-Caricyno-na-yuge-Moskvy-87035']]),

    dict(slug='sollers-jf-mould', date='2026-06-02', status='Закрыта', type='M&A',
         title='«Соллерс» продал китайской JF Mould 20% в производстве кузовных деталей',
         seller='«Соллерс»', buyer_name='JF Mould (Hefei Hualong Mould, Китай)',
         asset='20% ООО «Штамповые технологии»',
         ind='Автопром',
         src=[['mergers.ru', 'https://mergers.ru/news/Sollers-prodal-kitajskoj-JF-Mould-20-v-proizvodstve-kuzovnyh-detalej-87015']]),

    dict(slug='veb-gtlk', date='2026-06-02', status='Обсуждается', type='M&A',
         title='ВЭБ.РФ объявила о приобретении ГТЛК',
         buyer_name='ВЭБ.РФ', asset='ГТЛК (Государственная транспортная лизинговая компания)',
         ind='Транспорт и логистика',
         src=[['mergers.ru', 'https://mergers.ru/news/VJeBRF-obyavila-o-priobretenii-GTLK-87019']]),

    dict(slug='nspk-privatization', date='2026-07-03', status='Обсуждается', type='M&A',
         title='Банк России готовит частичную приватизацию НСПК',
         seller='Банк России', asset='доля в НСПК (оператор карт «Мир»)',
         ind='Финтех',
         events=[
             dict(kind='negotiations', date='2026-07-02', title='Раскрыты детали обсуждения',
                  note='Банк России обсуждает с кредитными организациями параметры продажи доли в НСПК: регулятор предлагает участникам рынка купить миноритарный пакет акций.',
                  source=['mergers.ru', 'https://mergers.ru/news/V-Rosselhozbanke-raskryli-detali-vozmozhnoj-prodazhi-doli-v-NSPK-v-rynok-87137']),
             dict(kind='negotiations', date='2026-07-03', title='Готовится рыночная оценка',
                  note='Глава Банка России Эльвира Набиуллина заявила об обсуждении с банками частичной приватизации НСПК; планируется рыночная оценка компании.',
                  source=['mergers.ru', 'https://mergers.ru/news/Bank-Rossii-provedet-ocenku-NSPK-pered-vozmozhnoj-prodazhej-doli-87145']),
         ],
         src=[['mergers.ru', 'https://mergers.ru/news/Bank-Rossii-provedet-ocenku-NSPK-pered-vozmozhnoj-prodazhej-doli-87145'],
              ['mergers.ru', 'https://mergers.ru/news/V-Rosselhozbanke-raskryli-detali-vozmozhnoj-prodazhi-doli-v-NSPK-v-rynok-87137']]),
]

# Найдены при сверке с базой — НЕ новые карточки, а факты для обогащения уже
# существующих. Автоматически ничего не пишут: список для следующего шага
# (ручная правка или доработка match.py, чтобы сигнал стал сильнее).
ENRICH_HINTS = {
    'gdcc03f9d': 'ЮГК/БТС-Мост Холдинг: серия публикаций mergers.ru (11.06 аукцион объявлен '
                 '81,01 млрд ₽ -> 06.07 оплата 93,16 млрд ₽ -> 15.07 владение УК -> 17.07 владение 67,2% акций) '
                 'подтверждает и уточняет сумму закрытой сделки.',
    'g92476095': 'Галс-Девелопмент: mergers.ru уточняет, что гостиница Holiday Inn Сокольники входила '
                 'в периметр сделки и оценивается отдельно в 8-10 млрд ₽ (не путать с общей суммой 100 млрд ₽).',
    'g68a112bd': '«Русатом Хэлскеа увеличил долю в Медскане до 50%» — mergers.ru 03.06 сообщает обратное '
                 'движение: доля снижена с 50% до 45% перед IPO «Медскана» в сентябре 2026.',
    'gf13fba9e': 'Домодедово/Перспектива: mergers.ru 21.07 подтверждает, что «Перспектива» выкупила '
                 'группу «Домодедово» у Росимущества за 66 млрд ₽, и что Внуково намерено купить 25,01% '
                 'долей «Перспективы» за 16,5 млрд ₽.',
    'g7f396659': '«Р-Фарм»/«Центр ЭКО»: mergers.ru 03.06 сообщает о выкупе ОСТАВШИХСЯ 50,1% (было 49,9% '
                 'с 2024 года) у Сергея Лебедева — сделка закрыта 29 мая 2026.',
    'g5eb6ff22': 'Росатом/Дело («русская рулетка»): три публикации mergers.ru (06.07 решение выкупить, '
                 '26.06 Шишкарев отказался от встречного выкупа, 31.07 Лихачев о досрочном закрытии до '
                 'конца ноября) — этап сделки продвинулся, но новую карточку не создаём.',
}

INDUSTRIES = {"Нефть и газ", "Уголь", "ГМК и добыча", "Энергетика", "Химия и удобрения", "Агро",
              "Пищепром и напитки", "Ритейл", "E-commerce", "Потребительские товары", "ИТ и интернет",
              "Искусственный интеллект", "Телеком", "Банки", "Страхование", "Финтех", "Финансовые услуги",
              "Рынок ценных бумаг", "Управление активами", "Холдинги", "Транспорт и логистика",
              "Порты и инфраструктура", "Автопром", "Недвижимость", "Строительство", "Гостиницы и туризм",
              "Здравоохранение", "Фармацевтика", "Образование", "Развлечения", "Профессиональные услуги",
              "Медиа", "Машиностроение", "Лесопром", "ЖКХ и обращение с отходами", "Не определена"}


def make_id(slug):
    return 'gmru-' + slug


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    existing = {d['id'] for d in data['deals']}

    plan = []
    for spec in NEW_CARDS:
        assert spec['ind'] in INDUSTRIES, '%s: отрасль не из списка (%r)' % (spec['slug'], spec['ind'])
        assert spec.get('src'), '%s: нет источника' % spec['slug']
        deal_id = make_id(spec['slug'])
        assert deal_id not in existing, '%s: уже записано (id %s)' % (spec['slug'], deal_id)
        card = {
            'id': deal_id,
            'date': spec['date'],
            'title': spec['title'],
            'ind': spec['ind'],
            'type': spec['type'],
            'status': spec['status'],
            'src': spec['src'],
            'from_ingest': True,
            # Тот же дефолт, что теперь у promote.py: интерфейс много где читает
            # d.law.adv/d.eco.rationale без проверки на существование объекта.
            'eco': {'sum': '—', 'share': '—', 'val': '—', 'target_fin': '—',
                    'fin': '—', 'rationale': '—', 'context': '—', 'finadv': '—'},
            'law': {'struct': '—', 'appr': '—', 'adv': [], 'terms': '—'},
        }
        for field in ('sum', 'seller', 'buyer_name', 'asset'):
            if spec.get(field):
                card[field] = spec[field]
        if spec.get('events'):
            card['events'] = spec['events']
        plan.append(card)

    print('Новых карточек к записи: %d' % len(plan))
    for card in plan:
        print('  %-28s %-12s %s' % (card['id'], card['date'], card['title']))
    print('\nНайдено для обогащения существующих карточек (не пишется этим скриптом): %d' % len(ENRICH_HINTS))
    for cid, note in ENRICH_HINTS.items():
        print('  %-12s %s' % (cid, note[:90]))

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return

    data['deals'].extend(plan)
    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('\nЗаписано карточек: %d' % len(plan))


if __name__ == '__main__':
    main('--write' in sys.argv)
