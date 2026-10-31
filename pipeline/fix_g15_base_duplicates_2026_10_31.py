# -*- coding: utf-8 -*-
"""G15 (31 октября 2026): разбор 135 подозрительных пар внутри базы.

`pipeline/base_duplicates_scan.py` проверяет карточки базы друг против друга
теми же правилами, что ворота притока (`match.is_strong`,
`promote.whole_base_twin`), и 31 октября 2026 нашел 135 пар. Каждая пара
прочитана по обеим карточкам (стороны, предмет, дата, сумма, источники; где
заголовков не хватало — статьи), и решение записано в таблице `PAIRS` ниже:

  merge      — одна сделка под двумя id: сливается общим скриптом
               `merge_duplicate_deals_batch.Merge` (остается более полная
               карточка; источники и пустые поля переезжают; `merged[drop] =
               keep`; `telegram_posts` переезжает; записи FIXES на удаленный
               id снимаются);
  stage      — та же сделка, но вторая карточка описывает другое событие ее
               жизни (слух → продажа, поиск покупателя → закрытие, пересмотр
               расчетов): сливается так же, а событие дописывается в
               `events[]` выжившей карточки с `id` вида «вид-дата», и старый
               адрес ведет прямо на этап через `merged_deal_stages`
               (так сделано у Ситибанка и «Аэрофлота»/«Аэромара»);
  drop_only  — карточка уже стоит в `merged`, но из `deals` не удалена
               (gd95bf2d7 → g5745c187): просто снимается;
  separate   — разные сделки (другой объект, другой покупатель, другой
               транш): обеим ставится `separate_transaction_reviewed=True`,
               чтобы пара больше не всплывала; два шага одной истории
               (сорвавшаяся продажа и ее исход, два пакета по 25%) кроме того
               связываются `related_deal_ids`, как «Тишинка» и 3S Group
               (`reconcile_duplicate_cards.py`);
  question   — решить без владельца нельзя (у обеих карточек свои посты в
               канале) — пара не трогается, вопрос уходит в консоль.

Сухой прогон печатает план и все отказы проверок; при любом отказе запись
не выполняется вовсе. С ключом --write база перечитывается прямо перед
записью, каждое действие держит `assert` на текущее состояние.

    python3 pipeline/fix_g15_base_duplicates_2026_10_31.py
    python3 pipeline/fix_g15_base_duplicates_2026_10_31.py --write
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'pipeline'))
import merge_duplicate_deals_batch as mdb  # noqa: E402

DATA = ROOT / 'static' / 'data' / 'deals_promoted.json'
SIGNALS = ROOT / 'static' / 'data' / 'signals.json'

# ---------------------------------------------------------------------------
# Таблица решений. Номер — порядковый номер пары в выводе
# base_duplicates_scan.py от 31 октября 2026.
# ---------------------------------------------------------------------------
PAIRS = [
    dict(n=1, a='baltika', b='ce6b8c447', kind='separate',
         why='сорванная продажа «Арнесту» (2023) и MBO через «ВГ Инвест» (2024) — разные сделки'),
    dict(n=2, a='c01291410', b='g3e7bc840', kind='separate', why='телеканалы «Медиа 1» (2024) и Gallery (2023)'),
    dict(n=3, a='c07bedf76', b='g029b7531', kind='stage', keep='g029b7531', drop='c07bedf76',
         stage='negotiations-2025-03-03',
         spec=dict(
             reason='Одна сделка: продажа «Газпром СПКА» структуре «Новый старт». c07bedf76 — слух марта 2025 '
                    '(«может продать»), g029b7531 — сама продажа 2026 года с пятью источниками.',
             add_src=[['Коммерсантъ', 'https://www.kommersant.ru/doc/7550441']],
             events=[dict(kind='negotiations', date='2025-03-03',
                          title='Обсуждается продажа доли в «Газпром СПКА»',
                          note='«Газпром» может продать «Роскосмосу» долю в «Газпром СПКА» — сборочном производстве '
                               'космических аппаратов. Предприятие введено в эксплуатацию в прошлом году, а участие '
                               'Роскосмоса способно обеспечить выпуск спутников для федеральных проектов. Главный '
                               'вопрос — финансирование сделки.',
                          source=['Коммерсантъ', 'https://www.kommersant.ru/doc/7550441'])])),
    dict(n=4, a='c0ea790b6', b='g3c230c8f', kind='merge', keep='g3c230c8f', drop='c0ea790b6',
         after={'date': ('2025', '2025-06-25')},
         spec=dict(
             reason='Одна сделка: «Атлант» («Трансфин-М») купил «Транслес» и «Грузовую компанию» у «Деметра-Холдинга». '
                    'У g3c230c8f предмет профилем, оценка суммы; у c0ea790b6 — точная дата 25 июня 2025 и третий источник.',
             add_src=[['Коммерсантъ', 'https://www.kommersant.ru/doc/7834211']])),
    dict(n=5, a='c171fe137', b='g25448b74', kind='merge', keep='g25448b74', drop='c171fe137',
         spec=dict(
             reason='Одна сделка: «Магнит» купил KazanExpress (объявлена 19 октября 2023, закрыта 9 ноября 2023). '
                    'c171fe137 — компактный импорт о закрытии; переносятся продавец профилем, три источника и этап закрытия.',
             set={'seller_id': 'g16938a37'},
             add_src=[['Orion', 'https://orion-law.com/news/orion-partners-vystupila-konsultantom-gruppy-kompanij-magnit-pri-priobretenii-marketplejsa-kazanexpress'],
                      ['ComNews', 'https://www.comnews.ru/content/230050/2023-11-09/2023-w45/1010/magnit-zakryl-sdelku-pokupke-kazanexpress'],
                      ['Коммерсантъ', 'https://www.kommersant.ru/doc/6323052']],
             events=[dict(kind='closed', date='2023-11-09', title='Сделка закрыта',
                          note='«Магнит» закрыл сделку по покупке 100% доли в маркетплейсе KazanExpress.',
                          source=['ComNews', 'https://www.comnews.ru/content/230050/2023-11-09/2023-w45/1010/magnit-zakryl-sdelku-pokupke-kazanexpress'])])),
    dict(n=6, a='c29710ac5', b='g549ddd5a', kind='merge', keep='g549ddd5a', drop='c29710ac5',
         spec=dict(reason='Одна сделка: «Эксойл» продал завод «Масленица» (экс-Bunge) ЭФКО. c29710ac5 — та же новость '
                          'Интерфакса, уже стоящая в источниках g549ddd5a; у выжившей покупатель профилем и четыре источника.')),
    dict(n=7, a='c51d0bb64', b='gffed92e4', kind='separate', why='WB Банк/ВТБ и «Дизайнмастер» — разные сделки'),
    dict(n=8, a='c6b59f911', b='g7d3f5a20', kind='separate', why='передача акций ДВМП «Росатому» (2024) и СП с DP World (2026)'),
    dict(n=9, a='cb30dbbc8', b='g5850b57f', kind='separate', why='СП с SolidSoft и объединение с VK Tech'),
    dict(n=10, a='cb30dbbc8', b='g596c8144', kind='separate', why='СП с SolidSoft и покупка DIKIDI'),
    dict(n=11, a='cc16fce80', b='g648505b0', kind='separate', why='ЮГК и «Метрогипротранс»'),
    dict(n=12, a='ccdd90216', b='g31136d69', kind='stage', keep='g31136d69', drop='ccdd90216',
         stage='announced-2024-12-26',
         spec=dict(
             reason='Одна сделка: O\'Key Group продала бизнес гипермаркетов «О\'Кей» менеджменту («РБФ ритейл»). '
                    'ccdd90216 — объявление декабря 2024, g31136d69 — закрытие 25 ноября 2025.',
             add_src=[['Коммерсантъ — «Сделки года»', 'https://www.kommersant.ru/doc/8077927'],
                      ['Интерфакс', 'https://www.interfax.ru/business/1000764'],
                      ["Shopper's", 'https://shoppers.media/news/19670_okei-grupp-prodast-biznes-gipermarketov-menedzmentu']],
             events=[dict(kind='announced', date='2024-12-26',
                          title='O\'Key Group объявила о продаже бизнеса гипермаркетов менеджменту',
                          note='Магазины, логистика и товарный знак — плюс остальные активы бизнеса, как материальные, так и нематериальные.',
                          source=['Интерфакс', 'https://www.interfax.ru/business/1000764'])])),
    dict(n=13, a='cdfe91cd0', b='g5eb6ff22', kind='separate', why='опцион до 49% (2022) и выкуп 51% (2026)'),
    dict(n=14, a='ce4180b68', b='g737a0487', kind='merge', keep='g737a0487', drop='ce4180b68',
         spec=dict(
             reason='Одна сделка: «Интер РАО» купил бизнес-центр «Московский шелк» у Sminex. ce4180b68 — заметка о '
                    'выставлении на продажу (апрель 2024) с суммой 4,8 млрд ₽ внутри диапазона выжившей (4,2–5 млрд ₽).',
             add_src=[['Ведомости', 'https://www.vedomosti.ru/realty/articles/2024/04/23/1033483-sminex-vistavila-na-prodazhu-chast-kvartala-moskovskii-shelk']],
             events=[dict(kind='other', date='2024-04-23', title='Sminex выставила бизнес-центр на продажу',
                          note='Девелопер выставляет на продажу бизнес-центр площадью 18 200 кв. м, построенный в 2009 году, '
                               '— часть комплекса «Московский шелк» на Саввинской набережной в Хамовниках, который он купил целиком.',
                          source=['Ведомости', 'https://www.vedomosti.ru/realty/articles/2024/04/23/1033483-sminex-vistavila-na-prodazhu-chast-kvartala-moskovskii-shelk'])])),
    dict(n=15, a='ce4fca919', b='ga0a49202', kind='merge', keep='ga0a49202', drop='ce4fca919',
         spec=dict(
             reason='Одна сделка: сеть квестов «Клаустрофобия» перешла от Александра Ручьева команде GrimTeam (три общих '
                    'источника; находка очереди аудита от 21 сентября 2026). У ga0a49202 покупатель и предмет профилями, '
                    'сумма 400 млн ₽; из ce4fca919 переносятся структура владения и два источника 2024 года.',
             append_extra='Сеть квестов «Клаустрофобия» перешла от прежнего владельца — президента ГК «Основа» Александра '
                          'Ручьева, владевшего сетью с 2019 года — команде конкурирующей сети GrimTeam: 1 августа 2025 года '
                          'учреждены два юрлица, «Клаустрофобия онлайн» и «Клаустрофобия офлайн», где 51% принадлежит '
                          'инвестору Вадиму Змовику, 33% — сооснователю GrimTeam Павлу Вараксину и 16% — Евгению Авину, '
                          'назначенному генеральным директором. Ранее рассматривалась продажа МТС Live и Яндексу, но '
                          'переговоры с МТС в итоге не привели к сделке — стороны не сошлись в цене и условиях.',
             add_src=[['РБК', 'https://www.rbc.ru/technology_and_media/27/08/2024/66cc760e9a794719ed48a5bd'],
                      ['Sostav.ru', 'https://www.sostav.ru/publication/set-kvestov-klaustrofobiya-proda-t-biznes-69680.html']],
             events=[dict(kind='negotiations', date='2024-08-27', title='Сеть выставлена на продажу',
                          note='Ранее рассматривалась продажа МТС Live и Яндексу, но переговоры с МТС в итоге не привели '
                               'к сделке — стороны не сошлись в цене и условиях.',
                          source=['РБК', 'https://www.rbc.ru/technology_and_media/27/08/2024/66cc760e9a794719ed48a5bd'])])),
    dict(n=16, a='ce7b84bec', b='g31546fef', kind='merge', keep='g31546fef', drop='ce7b84bec',
         spec=dict(
             reason='Одна сделка: АО «Управление активами» купило на торгах 100% «Юг Девелопмент» с кварталом '
                    '«Даниловская мануфактура» за 12,3 млрд ₽. У g31546fef стороны и предмет профилями; из ce7b84bec '
                    'переносятся пресс-релиз РАД, день торгов и сведения о покупателе.',
             append_extra='Учредители АО «Управлением активами» не раскрываются. По данным ЕГРЮЛ, гендиректор компании — '
                          'Кирилл Демченко; ему же принадлежит ООО «Кэпитал перформ», из состава учредителей которого '
                          'в 2022 году вышла Ксения Шойгу.',
             add_src=[['РАД (пресс-релиз)', 'https://auction-house.ru/media-portal/news/prodan-biznes-kvartal-danilovskaya-manufaktura/']],
             events=[dict(kind='other', date='2025-12-18', title='Торги: 100% «Юг Девелопмент» проданы за 12,3 млрд ₽',
                          note='На торги их выставили в ноябре «КР плюс» и «Сбербанк капитал».',
                          source=['РАД (пресс-релиз)', 'https://auction-house.ru/media-portal/news/prodan-biznes-kvartal-danilovskaya-manufaktura/'])])),
    dict(n=17, a='cf2375bf5', b='g003e4867', kind='separate', why='«Квартал Герцена» (2024) и «Рублевские кварталы» (2025) — разные проекты'),
    dict(n=18, a='g015e2da2', b='g5d835058', kind='separate', why='«Александрия» и «РУСMED» — разные клиники'),
    dict(n=19, a='g017cd5b4', b='g45a72968', kind='separate', why='инвестиция в «Моторику» и покупка «Моторикой» «Лимба»'),
    dict(n=20, a='g02eed099', b='gcdd2b6de', kind='separate', related=True,
         why='доля «Гермеса» в юрлицах OBI (апрель 2025) и покупка активов магазинов «Лентой» (январь 2026) — два шага одной истории'),
    dict(n=21, a='g04edfc17', b='g94dcc5cc', kind='separate', why='36% Tawazun → «Дедал» и 51% → «Газпром Тех»'),
    dict(n=22, a='g073bf58b', b='g0df6c7c4', kind='separate', why='BASF и Flint Group — разные продавцы и заводы'),
    dict(n=23, a='g076a2f4e', b='g6206d0f7', kind='separate', why='покупка «Жилкапинвеста» и IPO Glorax'),
    dict(n=24, a='g081ac83c', b='gdbb7d921', kind='separate', why='Hexway и Digital Security'),
    dict(n=25, a='g0931ce83', b='g672c6dfe', kind='merge', keep='g0931ce83', drop='g672c6dfe',
         spec=dict(
             reason='Одна сделка: Павел Те («Велна») вышел из «СМ», владеющего 25% Рязанской чаеразвесочной фабрики; '
                    'покупатели — Максим Буре и Ольга Шатрова. У g0931ce83 стороны и предмет профилями; '
                    'у g672c6dfe — пост 93 в канале, он переезжает.',
             add_src=[['Sostav.ru', 'https://www.sostav.ru/publication/pavel-t-vyshel-iz-biznesa-po-kontraktnomu-proizvodstvu-chaya-76972.html']])),
    dict(n=26, a='g097e34b2', b='g756f35a3', kind='separate', why='«Южгазэнерджи» (2026) и «Первая образцовая типография» (2023)'),
    dict(n=27, a='g0a0d451a', b='g61a8095f', kind='separate', why='Yum! Brands и AmRest — разные продавцы KFC'),
    dict(n=28, a='g0a6f7569', b='gecc48c49', kind='merge', keep='gecc48c49', drop='g0a6f7569',
         spec=dict(
             reason='Одна сделка: Qiwi купила RealWeb 7 декабря 2022 года (названа в docs/duplicates.md). У gecc48c49 '
                    'цена 1,77 млрд ₽ из отчета Qiwi и шесть источников; из g0a6f7569 переносятся продавцы и Forbes.',
             set={'seller': 'Совладельцы Realweb — Эмин и Олеся Аветисян, Василий Лазука, Максим Виноградов, '
                            'Иван Хмелевской, а также фонд iTech Capital'},
             append_extra='Свои доли продали все акционеры, включая фонд iTech Capital с 25%.',
             add_src=[['Forbes', 'https://www.forbes.ru/biznes/482340-qiwi-kupila-krupnogo-igroka-na-rynke-onlajn-reklamy']])),
    dict(n=29, a='g0dea398b', b='g927f3242', kind='separate', why='покупка Fazer (2022) и «Волжский пекарь» (2024)'),
    dict(n=30, a='g0fadc207', b='g6bccb70f', kind='stage', keep='g0fadc207', drop='g6bccb70f',
         stage='other-2025-12-23',
         spec=dict(
             reason='Одна сделка: продажа АО «КИВИ» Fusion Factor Fintech Limited (январь 2024). g6bccb70f — пересмотр '
                    'условий расчетов по той же сделке в декабре 2025 года: становится этапом.',
             append_extra='В декабре 2025 года совет директоров NanduQ (бывшая Qiwi plc) обновил соглашение с гонконгской '
                          'Fusion Factor Fintech Limited, принадлежащей бывшему гендиректору Qiwi Андрею Протопопову. '
                          'Вместо изначальных 23,75 млрд ₽ в рассрочку покупатель завершил расчеты, уплатив 4 млрд ₽ '
                          '(около $50,3 млн по курсу конца 2025 года) и передав 29,288 млн акций NanduQ класса B, '
                          'оцененных в диапазоне от $80,5 до $168,4 млн (6,3–13,2 млрд ₽ по курсу ЦБ на 24.12.2025). '
                          'Денежную часть NanduQ получила в марте 2026 года, передача акций завершилась в мае 2026 года.',
             add_src=[['Интерфакс', 'https://www.interfax.ru/business/1087961'],
                      ['Интерфакс', 'https://www.interfax.ru/business/1064716'],
                      ['Forbes.ru', 'https://www.forbes.ru/investicii/552686-nanduq-planiruet-peresmotret-uslovia-prodazi-rossijskogo-ao-kivi'],
                      ['CNews', 'https://www.cnews.ru/news/top/2025-12-24_posle_otzyva_bankovskoj'],
                      ['MarketPower', 'https://marketpower.pro/publications/pokupatel-aktivov-kivi-polnostiu-zavershil-raschety-s-kompaniei-nanduq'],
                      ['Коммерсантъ', 'https://www.kommersant.ru/doc/7835470'],
                      ['Право.ru', 'https://pravo.ru/news/254638/']],
             events=[dict(kind='other', date='2025-12-23', title='Пересмотр условий расчетов',
                          note='В декабре 2025 года совет директоров NanduQ (бывшая Qiwi plc) обновил соглашение с '
                               'гонконгской Fusion Factor Fintech Limited, принадлежащей бывшему гендиректору Qiwi Андрею '
                               'Протопопову. Вместо изначальных 23,75 млрд ₽ в рассрочку покупатель завершил расчеты, '
                               'уплатив 4 млрд ₽ (около $50,3 млн по курсу конца 2025 года) и передав 29,288 млн акций '
                               'NanduQ класса B, оцененных в диапазоне от $80,5 до $168,4 млн (6,3–13,2 млрд ₽ по курсу '
                               'ЦБ на 24.12.2025).',
                          source=['Интерфакс', 'https://www.interfax.ru/business/1087961'])])),
    dict(n=31, a='g10adb6ac', b='g41075b4e', kind='stage', keep='g10adb6ac', drop='g41075b4e',
         stage='approval-2023-11-27',
         spec=dict(
             reason='Одна сделка: активы Caterpillar («Катерпиллар Тосно» и «Катерпиллар Файненшл») перешли структуре '
                    'Balchug Capital через ООО «ПСК — Новые решения». g41075b4e — разрешение президента (ноябрь 2023), '
                    'g10adb6ac — закрытие (июнь 2024).',
             append_extra='Оба владельца покупателя пришли из Sberbank CIB. Ян Вейцман возглавлял там управление, которое '
                          'вело металлургических и горнодобывающих клиентов. Кирилл Полишкин занимал пост заместителя '
                          'директора в департаменте, отвечавшем за крупнейших клиентов.',
             add_src=[['Интерфакс', 'https://www.interfax.ru/russia/933466'],
                      ['Интерфакс', 'https://www.interfax.ru/business/969833']],
             events=[dict(kind='approval', date='2023-11-27', title='Президент разрешил передачу активов',
                          note='Оба владельца покупателя пришли из Sberbank CIB. Ян Вейцман возглавлял там управление, '
                               'которое вело металлургических и горнодобывающих клиентов. Кирилл Полишкин занимал пост '
                               'заместителя директора в департаменте, отвечавшем за крупнейших клиентов.',
                          source=['Интерфакс', 'https://www.interfax.ru/russia/933466'])])),
    dict(n=32, a='g10adb6ac', b='g934ee51b', kind='separate', why='другие юрлица Caterpillar («Евразия», «Солар Турбинс» и др., 2025)'),
    dict(n=33, a='g16a70078', b='gdda3e685', kind='separate', why='«Интеко» и «Инград»'),
    dict(n=34, a='g178fcbb1', b='g35c2f65e', kind='separate', why='разные участки Роснедр'),
    dict(n=35, a='g1a475dee', b='gdf51a7ca', kind='separate', why='«Решения Гармония» и «Убик»'),
    dict(n=36, a='g1cc071e4', b='gc6322659', kind='stage', keep='g1cc071e4', drop='gc6322659',
         stage='negotiations-2023-08-21',
         spec=dict(
             reason='Одна сделка: My.Games продала Boosty Павлу Харанеку (Broadsmart Group). gc6322659 — начало переговоров '
                    'о продаже (Интерфакс, 21 августа 2023), g1cc071e4 — сама продажа.',
             set={'sum': '4–10 млн $'},
             add_src=[['Интерфакс', 'https://www.interfax.ru/business/917057']],
             events=[dict(kind='negotiations', date='2023-08-21', title='My.Games начала переговоры о продаже Boosty',
                          note='My.Games ищет покупателя для платформы монетизации контента Boosty. Саму платформу My.Games, '
                               'бывшее игровое подразделение VK, купила у VK осенью 2022 года.',
                          source=['Интерфакс', 'https://www.interfax.ru/business/917057'])])),
    dict(n=37, a='g1d76aeb5', b='g79f683bc', kind='separate', related=True,
         why='Multispace (2023) и «Фонбет» (2025) — разные несостоявшиеся покупатели одного БЦ'),
    dict(n=38, a='g1dc82018', b='g3e3f5e9c', kind='separate', why='лифтовый завод и КПСК — разные активы СУ-155'),
    dict(n=39, a='g1e2b16c3', b='g28f1d233', kind='separate', why='завод Bridgestone (2023) и продажа «Кордианта» (2024)'),
    dict(n=40, a='g1f2895c0', b='g8a8ae3f7', kind='separate', why='20% «Юниреста» и 12,75% IRB'),
    dict(n=41, a='g1f8414a3', b='g5b4e85aa', kind='separate', why='банк и агробизнес — разные лоты ПСБ'),
    dict(n=42, a='g211615eb', b='gdde6bef5', kind='separate', why='Eleven и слияние с Whoosh'),
    dict(n=43, a='g21ef1542', b='ge7ec25e7', kind='separate', why='штаб-квартира в Химках и склад в Есипово'),
    dict(n=44, a='g22d3599c', b='g87583786', kind='separate', why='разные лоты КРТ'),
    dict(n=45, a='g23592800', b='gafda8e29', kind='separate', why='заводы бытовой техники и площадки в Энгельсе'),
    dict(n=46, a='g24e6d8ee', b='g5eb6ff22', kind='separate', related=True,
         why='несостоявшееся СП с ТМХ (2024–2025) и выкуп 51% «Росатомом» (2026) — два шага одной истории'),
    dict(n=47, a='g24e6d8ee', b='gece30945', kind='separate', why='«Дело» и индийское СП ТМХ'),
    dict(n=48, a='g253252c4', b='g420352ff', kind='separate', why='разные лоты КРТ'),
    dict(n=49, a='g253252c4', b='g87583786', kind='separate', why='разные лоты КРТ'),
    dict(n=50, a='g25a6766d', b='ge6e9c77a', kind='separate', why='Baggins Coffee и One & Double'),
    dict(n=51, a='g25db4ede', b='g3074f98b', kind='separate', why='Ivideon и фонд Норвегии'),
    dict(n=52, a='g282be68a', b='g8de46135', kind='stage', keep='g282be68a', drop='g8de46135',
         stage='negotiations-2023-08-16',
         spec=dict(
             reason='Одна сделка: топ-менеджеры Faurecia («Формат Инвест») выкупили тольяттинские площадки. g8de46135 — '
                    'поиск покупателя (август 2023), g282be68a — закрытие 10 января 2024.',
             append_extra='Faurecia ищет покупателей на свои российские заводы. Претендуют топ-менеджеры российского '
                          'подразделения компании и группа «Автокомпонент». В продажу входят производственные площадки '
                          'в Тольятти, Санкт-Петербурге, Калуге и Ленинградской области.',
             add_src=[['Коммерсантъ', 'https://www.kommersant.ru/doc/6161278']],
             events=[dict(kind='negotiations', date='2023-08-16', title='Faurecia ищет покупателей на российские заводы',
                          note='Faurecia ищет покупателей на свои российские заводы. Претендуют топ-менеджеры российского '
                               'подразделения компании и группа «Автокомпонент». В продажу входят производственные '
                               'площадки в Тольятти, Санкт-Петербурге, Калуге и Ленинградской области.',
                          source=['Коммерсантъ', 'https://www.kommersant.ru/doc/6161278'])])),
    dict(n=53, a='g282be68a', b='gd38acdec', kind='separate', why='перепродажа 50% ФЭР «Русатом Химии»'),
    dict(n=54, a='g28f1d233', b='g4a751f95', kind='merge', keep='g4a751f95', drop='g28f1d233',
         spec=dict(
             reason='Одна сделка: «Севергрупп» купила «Кордиант» у S8 Capital 1 октября 2024 (названа в docs/duplicates.md: '
                    'заведена повторно 18 сентября 2026). У g4a751f95 пять источников и перечень брендов.',
             add_src=[['Ведомости', 'https://www.vedomosti.ru/business/articles/2024/10/02/1066066-severgrupp-kupila-kordiant'],
                      ['Коммерсантъ', 'https://www.kommersant.ru/doc/7198179']])),
    dict(n=55, a='g2a27e6b5', b='gbf0be72c', kind='separate', why='«РН Банк» и «РНЛ Лизинг»'),
    dict(n=56, a='g2a4e8a51', b='g937b94f4', kind='separate', why='«Розовая коза» и Vet Union'),
    dict(n=57, a='g2bb8cf3a', b='gcaa03820', kind='separate', why='СМП-банк и «Атом»'),
    dict(n=58, a='g2ecf6ee9', b='g381ff192', kind='separate', related=True,
         why='доверительное управление госпакетом БСК (2023) и покупка 57,43% «Росхимом» (2025) — два шага одной истории'),
    dict(n=59, a='g2f5143f4', b='g672dcca1', kind='separate', why='Шереметьево и НМТП'),
    dict(n=60, a='g34cab70b', b='gc82185e7', kind='separate', why='«Центральное» и элеватор «БиоТехнологии»'),
    dict(n=61, a='g352131ac', b='g97e55758', kind='separate', why='Быстринско-Ширинское и РНК'),
    dict(n=62, a='g3555ea6e', b='gdc4ff4ab', kind='separate', related=True,
         why='34,96% Velle Петру Жукову (2023) и продажа «Логике молока» (2026)'),
    dict(n=63, a='g35c2f65e', b='gba4f7340', kind='separate', why='разные участки Роснедр'),
    dict(n=64, a='g37737226', b='g9f6fe860', kind='merge', keep='g9f6fe860', drop='g37737226',
         spec=dict(
             reason='Одна сделка: Selectel купил «Единую сеть» (servers.ru) 25 декабря 2024 (названа в docs/duplicates.md). '
                    'У g9f6fe860 точная сумма 3,045 млрд ₽, продавцы и дата; из g37737226 переносятся текст и четыре источника.',
             set={'extra': 'Selectel купил 100% ООО «Единая сеть», которому принадлежат бренды Servers.ru, Exepto.ru и '
                           'Fozzy.ru. Ходатайство о сделке подано в ФАС.',
                  'kind': 'acquisition'},
             add_src=[['РБК', 'https://www.rbc.ru/rbcfreenews/675fd25f9a7947b26cbfc66d'],
                      ['Selectel', 'https://selectel.ru/about/newsroom/news/selectel-soobshchaet-o-priobretenii-oblachnogo-provajdera-servers-ru/'],
                      ['runet.news', 'https://runet.news/articles/60778'],
                      ['Selectel', 'https://selectel.ru/about/newsroom/news/vyruchka-selectel-sostavila-183-mlrd-rublej-po-itogam-2025-goda/']])),
    dict(n=65, a='g39752167', b='gd88cbe9a', kind='separate', why='активы Kinross и «Гейзер Голд»'),
    dict(n=66, a='g3aa57efe', b='ged395e90', kind='separate', why='«Вельта-Пенза» и «Злаки на завтрак»'),
    dict(n=67, a='g3b9c077a', b='gff6e08fe', kind='separate', why='9,99% «Сбербанк инвестициям» (2023) и покупка Туголуковым (2024)'),
    dict(n=68, a='g3bcf9780', b='g7fac547e', kind='separate', why='Umnico и «ТДМ ТЕХ»'),
    dict(n=69, a='g3c46e216', b='g5c0f70c6', kind='separate', why='три завода упаковки и Сыктывкарский ЛПК'),
    dict(n=70, a='g3d73bbfc', b='gcf0f7334', kind='separate', why='Pilkington/NSG и AGC'),
    dict(n=71, a='g3db7d882', b='g4f24faca', kind='separate', why='«Кашин луг» и «Никольское»'),
    dict(n=72, a='g424715f8', b='g889e051d', kind='separate', related=True,
         why='22,5% «Восхода» «Краунинвесту» (2023) и передача контроля Милане Керимовой (2024)'),
    dict(n=73, a='g433cfd40', b='gfa47c307', kind='separate', why='«Столичные аптеки» и «Аптеки миницен»'),
    dict(n=74, a='g4612b667', b='ga13c3ea7', kind='separate', related=True,
         why='две части единого выхода Viterra: операционный бизнес и 50% терминала «Тамань» — разные покупатели'),
    dict(n=75, a='g47844a63', b='gff35947d', kind='separate', why='DocMed и Noun'),
    dict(n=76, a='g49c52cd4', b='g83ad1f72', kind='separate', why='«Про технолоджиз» и «Чемодан Про»'),
    dict(n=77, a='g4b78d957', b='g896a22ba', kind='separate', why='активы «РТ-Инвеста» и дом в Нерехте'),
    dict(n=78, a='g4ba9150f', b='g5bb3e777', kind='separate', related=True,
         why='Essity → «Новые технологии» (2023) и «ЭвоКом» → Светогорский ЦБК (2025)'),
    dict(n=79, a='g4c3f2103', b='g57ec9504', kind='separate', related=True,
         why='СП «Гвардеец» (Ъ, 14 апреля 2023) и «Сергиевское» + «Хуторок» (АК&М, 27 июля 2023) — разные юрлица'),
    dict(n=80, a='g4e3ec471', b='gdb854428', kind='merge', keep='gdb854428', drop='g4e3ec471',
         spec=dict(
             reason='Одна сделка: «Сбербанк инвестиции» купили 100% «СДМ ТК-2» (склад «Пивдома») у ЗПИФ «Азимут-капитал». '
                    'g4e3ec471 — новость юрфирмы Orion о той же сделке; переносятся консультанты и два источника.',
             append_extra='Сделку сопровождала команда корпоративной и финансовой практики Orion: партнер Евгений Зеленский, '
                          'старшие юристы Екатерина Палагина, Эльвира Ваниева и Дмитрий Мазуров, юристы Николай Дерунов '
                          'и Роман Гарькуша, помощник юриста Марсель Яппаров. Юристы готовили документы, вели переговоры, '
                          'подписывали и закрывали сделку.',
             add_src=[['Orion', 'https://orion-law.com/news/komanda-orion-konsultirovala-ooo-sberbank-investicii-v-sdelke-po-priobreteniyu-100-dolej-ooo-sdm-tk-2-i-dalnejshej-prodazhe-50-dolej-ooo-logopark-7'],
                      ['Коммерсантъ', 'https://www.kommersant.ru/doc/8077927']])),
    dict(n=81, a='g53656f7a', b='gb0d1c79e', kind='separate', why='«Союз-ТТМ» и комплекс «Союз-М»'),
    dict(n=82, a='g54dc2165', b='gc79e6178', kind='separate', why='oneFactor и Nexign'),
    dict(n=83, a='g56d19a38', b='gc302c18e', kind='separate', why='«Капитал МС» и «Капитал Life»'),
    dict(n=84, a='g5745c187', b='gd95bf2d7', kind='drop_only', keep='g5745c187', drop='gd95bf2d7',
         why='gd95bf2d7 уже стоит в merged → g5745c187, но из deals не удалена; единственный источник уже у выжившей'),
    dict(n=85, a='g577a83e0', b='g5e21a38a', kind='separate', why='«Аптека25.рф» и «Фарм»'),
    dict(n=86, a='g5880d206', b='gd1130c05', kind='separate', why='«Фольксваген банк Рус» и «Фольксваген Груп Рус»'),
    dict(n=87, a='g5c0f70c6', b='ge9d2a3e6', kind='separate', related=True,
         why='несостоявшаяся продажа ЛПК Augment (2022) и продажа «Сезар Групп» (2023)'),
    dict(n=88, a='g5c3eeb06', b='ga5b07998', kind='separate', why='Sberbank Europe и HSBC'),
    dict(n=89, a='g5e21a38a', b='g709c335a', kind='separate', why='«Фарм» и «Аптечество»'),
    dict(n=90, a='g60c082cf', b='gb1e062d2', kind='separate', related=True,
         why='RBI (2023, не состоялась) и «Кама Капитал» (2026) — разные покупатели San Gally Park'),
    dict(n=91, a='g60fedbfd', b='g91281c36', kind='separate', why='«Фармакон» и «Трика»'),
    dict(n=92, a='g6168731b', b='g64eb0e04', kind='merge', keep='g64eb0e04', drop='g6168731b',
         spec=dict(
             reason='Одна сделка: Heineken продал российский бизнес «Арнесту» за 1 евро (25 августа 2023). У g64eb0e04 '
                    'предмет профилем ООО «ОПХ» и условия; из g6168731b переносятся цена ухода и пять источников.',
             append_extra='Уход с рынка обошелся компании примерно в €0,4 млрд обесценения и неденежных расходов и около '
                          '300 млн евро потерь.',
             add_src=[['Коммерсантъ', 'https://www.kommersant.ru/amp/5941014'],
                      ['Ведомости', 'https://www.vedomosti.ru/business/articles/2023/08/25/991930-heineken-prodala-rossiiskii-biznes'],
                      ['Интерфакс', 'https://www.interfax.ru/business/917760'],
                      ['Коммерсантъ', 'https://www.kommersant.ru/doc/6379867'],
                      ['Коммерсантъ', 'https://www.kommersant.ru/doc/8161535']])),
    dict(n=93, a='g62698716', b='g8fb922a6', kind='separate', why='«Сименс Финанс» и БЦ «Легион II»'),
    dict(n=94, a='g656645d5', b='ksk', kind='merge', keep='ksk', drop='g656645d5',
         spec=dict(
             reason='Одна сделка: ГК «Дело» выкупила у Cargill 25% + 1 акцию КСК 8 февраля 2024 (A24 бэклога). '
                    'У ksk предмет и условия; из g656645d5 переносятся вид сделки и два источника.',
             set={'kind': 'acquisition'},
             add_src=[['oleoscope.com', 'https://oleoscope.com/news/zernovoj-terminal-gk-delo-v-novorossijske'],
                      ['Expert.ru', 'https://expert.ru/news/gk-delo-priostanovila-rabotu-zernovogo-terminala-v-novorossiyske']])),
    dict(n=95, a='g65d042bc', b='g9fed3cb1', kind='separate', why='долги «Сокры» и права требования к застройщику'),
    dict(n=96, a='g672dcca1', b='g941f2b2b', kind='separate', why='НМТП и Корсаковский порт'),
    dict(n=97, a='g69dbe10b', b='g73a51452', kind='separate', why='«Лунное» и Тенкергин'),
    dict(n=98, a='g6bccb70f', b='gcdec4f24', kind='separate', why='«Киви» и «Адамас» (g6bccb70f сливается в g0fadc207)'),
    dict(n=99, a='g6be1ac50', b='g88d5e740', kind='merge', keep='g6be1ac50', drop='g88d5e740',
         spec=dict(
             reason='Одна сделка: НЛМК продал сортовой дивизион ПМХ («Промсорт») 6 сентября 2023. У g6be1ac50 подробный '
                    'текст и покупатель профилем ПМХ; из g88d5e740 переносятся одобрение ФАС и два источника.',
             append_extra='Покупателем стало ООО «Промсорт», структура Евгения Зубицкого (ПМХ); ФАС одобрила сделку '
                          '21 сентября 2023 года.',
             add_src=[['Ведомости', 'https://www.vedomosti.ru/business/articles/2023/02/17/963336-nlmk-dogovarivaetsya-o-prodazhe-svoih-zavodov'],
                      ['kaluga-poisk.ru', 'https://www.kaluga-poisk.ru/news/ekonomika/fas-razreshila-prodazhu-zavoda-nlmk-kaluga-i-vtorchermet-nlmk']],
             events=[dict(kind='approval', date='2023-09-21', title='ФАС одобрила сделку',
                          note='Покупателем стало ООО «Промсорт», структура Евгения Зубицкого (ПМХ); ФАС одобрила сделку '
                               '21 сентября 2023 года.',
                          source=['kaluga-poisk.ru', 'https://www.kaluga-poisk.ru/news/ekonomika/fas-razreshila-prodazhu-zavoda-nlmk-kaluga-i-vtorchermet-nlmk'])])),
    dict(n=100, a='g6d711306', b='gbcf07c78', kind='merge', keep='gbcf07c78', drop='g6d711306',
         spec=dict(
             reason='Одна сделка: «Вымпелком» выставил на торги 2,9 тыс. кв. м офисного здания на 1-й Тверской-Ямской '
                    '(торги 21 октября 2026). g6d711306 — та же новость три дня спустя; у gbcf07c78 три источника и условия торгов.',
             add_src=[['CNews', 'https://www.cnews.ru/news/top/2026-10-05_bilajn_prodaet_svoj_ofis']])),
    dict(n=101, a='g6fc4d4ac', b='g7e90c94a', kind='separate', why='логопарк FM Logistic (2023) и склад Ghelamco (2025)'),
    dict(n=102, a='g713c9c18', b='gbb0a5366', kind='separate', why='50% Avito и «Румбери»'),
    dict(n=103, a='g73dba9d6', b='gffe3c2d0', kind='question',
         why='одна сделка (ЗПИФ «ВИМ Недвижимость» купил БЦ «Фрейм» у Forma), но у обеих карточек свои посты '
             'в канале (130 и 132) — какой пост остается за сделкой, решает владелец'),
    dict(n=104, a='g749a7844', b='gbdefd889', kind='separate', why='Малый пр. П.С. и Шкиперский проток — разные участки'),
    dict(n=105, a='g7596ae81', b='gac4491d6', kind='separate', why='аутлеты и БЦ «Метрополис»'),
    dict(n=106, a='g76f31c63', b='gb31c796f', kind='separate', related=True,
         why='две перепродажи «Ла дача Астрахань» за три недели: Полетаева → Дубовицкая → «Акашевская»'),
    dict(n=107, a='g7cb5d8f8', b='g9fdcb59d', kind='separate', why='Borjomi и Альфа-Банк Украина'),
    dict(n=108, a='g81a766ac', b='g97d9fa60', kind='separate', related=True,
         why='25% «Агро-Белогорья» по решению суда (сентябрь 2024) и выкуп остальных долей за 31 млрд ₽ (ноябрь 2024)'),
    dict(n=109, a='g833a29f6', b='gb83b2a3f', kind='separate', why='«Эксперт» и клиники в Сургуте'),
    dict(n=110, a='g835eac98', b='ga58eb450', kind='separate', why='СП в Гане и завод в Индии'),
    dict(n=111, a='g88304d3a', b='ge29c8b25', kind='separate', why='разные раунды MVS'),
    dict(n=112, a='g8c32cefd', b='gafda8e29', kind='separate', related=True,
         why='Bosch → S8 Capital (2023) и S8 Capital → «Севергрупп» (2024)'),
    dict(n=113, a='g8e027018', b='gf70a43e6', kind='separate', why='«Биннофарм» и «Вертекс»'),
    dict(n=114, a='g8e325ef9', b='gde280a8d', kind='separate', why='портфель логопарков PNK Rental и PNK Park Медведково'),
    dict(n=115, a='g926d097b', b='gba72051d', kind='separate', why='«Приосколье» и «Юг Руси»'),
    dict(n=116, a='g926d097b', b='gcb875d9e', kind='separate', related=True,
         why='Бобрицкий → «Инвест-трейд» (февраль 2025) и «Инвест-трейд» → «Агрокомплекс» (октябрь 2025)'),
    dict(n=117, a='g931e89e1', b='gfcfba8c9', kind='separate', related=True,
         why='два объекта одного лота: ТЦ «Аура» в Сургуте (опровергнута) и в Ярославле (продана)'),
    dict(n=118, a='g937b94f4', b='ge816c5b4', kind='separate', why='Vet Union и Western Union'),
    dict(n=119, a='g96da922c', b='ga4d82b1c', kind='merge', keep='g96da922c', drop='ga4d82b1c',
         spec=dict(
             reason='Одна сделка: Danone продала российский бизнес «Вамин Р» (названа в docs/duplicates.md). '
                    'У g96da922c восемь источников и этап одобрения; из ga4d82b1c переносятся четыре источника.',
             add_src=[['Интерфакс', 'https://www.interfax.ru/business/961100'],
                      ['Интерфакс', 'https://www.interfax.ru/business/996657'],
                      ['Meduza', 'https://meduza.io/news/2025/10/08/rossiyskiy-danone-stal-logikoy-moloka'],
                      ['New Retail', 'https://new-retail.ru/novosti/retail/logika_moloka_investiruet_v_proizvodstvo_bolee_120_mlrd_rubley_do_2030_goda/']])),
    dict(n=120, a='g97e1f483', b='gb84f2b2f', kind='separate', why='«Здоровый город» и «Трик Фарма»'),
    dict(n=121, a='ga09376f6', b='ga1f2b443', kind='separate', why='«Стаксель» и «Датана»/«Датабриз»'),
    dict(n=122, a='ga1935680', b='gcdd2b6de', kind='merge', keep='gcdd2b6de', drop='ga1935680',
         spec=dict(
             reason='Одна сделка: «Гермес» («Севергрупп») получил 65% российских юрлиц OBI у «Синдики» (2025). '
                    'У gcdd2b6de продавец профилем и семь источников; из ga1935680 переносятся разрешение и два источника.',
             append_extra='«Гермесу» разрешено приобрести 65% в российском бизнесе сети строительных гипермаркетов OBI. '
                          'Нового владельца связывают с «Севергрупп».',
             add_src=[['BFM.ru', 'https://www.bfm.ru/news/575273'],
                      ['dp.ru', 'https://www.dp.ru/a/2025/07/14/germes-priobrjol-65-dolej']])),
    dict(n=123, a='ga24ad083', b='ga8d7e0ee', kind='separate', why='особняки в Белорецке и Сыктывкаре'),
    dict(n=124, a='ga5a7f3c1', b='ge283bafc', kind='separate', why='Aspace и Multispace'),
    dict(n=125, a='gab0f3dde', b='mercedes', kind='separate', why='активы Mercedes-Benz (2023) и перепродажа лизинговой «дочки» (2026)'),
    dict(n=126, a='gac4491d6', b='gd75ae46f', kind='separate', why='бизнес-центр и ТРЦ «Метрополис» — разные объекты и покупатели'),
    dict(n=127, a='gb1efa21d', b='gfd5e2810', kind='separate', why='M1Cloud и Rnet'),
    dict(n=128, a='gb2d5da8c', b='gf0ce42ac', kind='merge', keep='gf0ce42ac', drop='gb2d5da8c',
         stage='closed-2026-05-28',
         spec=dict(
             reason='Одна сделка: Александр Орехов выкупил 40% ГК «Азот» у Светланы Рыбальченко (закрыта 28 мая 2026). '
                    'У gf0ce42ac вся история с 2024 года и этап закрытия; из gb2d5da8c переносятся мотив и источник.',
             append_extra='Структуры Александра Орехова консолидировали 100% акционерного капитала ГК «Азот» — одного из '
                          'крупнейших производителей азотных удобрений в России, выкупив 40% акций у Светланы Рыбальченко. '
                          'Консолидация упрощает принятие решений по строительству газохимического комплекса в Воркуте '
                          'с инвестициями около 200 млрд ₽.',
             add_src=[['abireg.ru', 'https://abireg.ru/newsitem/114584/']])),
    dict(n=129, a='gbe0ffe61', b='gdc72cc35', kind='separate', why='ХКФ Банк и «ППФ Страхование жизни»'),
    dict(n=130, a='gc5951fac', b='gd4728207', kind='separate', why='CARGO.RUN и CargoTech'),
    dict(n=131, a='gcfae418d', b='gfda775ad', kind='separate', why='ЮМГ и центр в Солнцево'),
    dict(n=132, a='gd1130c05', b='geb645292', kind='separate', why='«Фольксваген Груп Рус» и финансовые «дочки»'),
    dict(n=133, a='gd3ba954d', b='gf9932079', kind='separate', related=True,
         why='два пакета «Просвещения» по 25% у разных продавцов («Сбер», «Инвест Про»)'),
    dict(n=134, a='gd73fd825', b='gf87a65f7', kind='separate', related=True,
         why='заявки Потанина и Алекперова (2023, не состоялась) и сделка консорциума (2024)'),
    dict(n=135, a='gd937c845', b='ge816c5b4', kind='separate', why='ОТП Банк и Western Union'),
]


# ---------------------------------------------------------------------------
# Поля дубля, пустые у выжившей карточки (правило docs/duplicates.md: «из
# дубля переносятся источники и поля, пустые у выжившей; уникальные факты —
# в поля, а не только ссылкой»). Тексты дословно из удаляемых карточек —
# `Merge.check` отказывает любому предложению, которого нет ни в одной из
# двух карточек, и любому полю, где у выжившей уже есть содержание.
# Не переносятся: `buyer_name`, когда у выжившей покупатель профилем;
# «обоснование», которое на деле описывает консультанта.
# ---------------------------------------------------------------------------
FIELD_TRANSFERS = {
    'c0ea790b6': {
        'law.struct': 'В сделку вошли 100% долей ООО «ТрансЛес» — двумя пакетами, 51% и 49%, — и 100% «Грузовой компании».',
    },
    'c171fe137': {
        'eco.share': '100% доли в маркетплейсе KazanExpress',
        'eco.rationale': '«Магнит» быстро заходит в маркетплейсы — новый для себя и быстро растущий сегмент, где хочет занять значимую долю. Купить готовую площадку быстрее и дешевле, чем строить свою с нуля.',
        'eco.context': 'KazanExpress продавали сразу несколько владельцев. Среди них — основатели маркетплейса Линар Хуснуллин и Кевин Ханда, а также владелец казанского холдинга FIX Сергей Еремеев. Еще один продавец — «Агрегатор-онлайн», структура «AliExpress Россия».',
        'law.appr': 'Сделка была одобрена Федеральной антимонопольной службой России.',
        'law.terms': 'KazanExpress будет работать внутри «Магнита» как отдельное бизнес-подразделение под руководством текущего менеджмента. 9 января 2024 года состоялся официальный ребрендинг KazanExpress в «Магнит Маркет». По итогам 2024 года показатели площадки заметно просели по сравнению с прежним KazanExpress: оборот снизился почти на четверть, до 13,4 млрд ₽, число заказов упало на 34%, до 14,4 млн, а чистый убыток вырос до 3,22 млрд ₽ (против 1,47 млрд ₽ в 2023 году).',
    },
    'c29710ac5': {
        'eco.rationale': 'Exoil Group уходит с внутреннего рынка и сосредотачивается на экспорте — так совладелец группы Карен Ванецян объясняет продажу.',
        'law.terms': 'Разрешение ФАС выдано вместе с предписанием, которое действует пять лет от даты сделки. Компания обязана не меньше 10% всех закупок подсолнечника проводить через биржу, регулярно подавая заявки. О каждом подъеме оптово-отпускных цен на 10% и выше нужно сообщать в службу и объяснять причины. Кроме того, для фасованного подсолнечного масла на внутреннем рынке покупатель должен составить торгово-сбытовую политику, опубликовать ее на своем сайте и соблюдать.',
    },
    'ccdd90216': {
        'eco.target_fin': "На конец сентября 2024 года у группы «О'Кей» было 77 гипермаркетов и 220 дискаунтеров. За 9 месяцев 2024 года ее чистая розничная выручка выросла на 5,6%, до 155,6 млрд ₽. Гипермаркеты дали 102,7 млрд ₽ (+1,6% год к году), дискаунтеры — 52,9 млрд ₽ (+14,3%).",
        'law.struct': 'Долг сети составляет 45,9 млрд рублей. По неофициальным сведениям, из-за высокой долговой нагрузки передача бизнеса «О`кей» менеджменту может оказаться фактически безденежной.',
    },
    'ce4fca919': {
        'eco.share': 'Покупатели — новые ООО «Клаустрофобия онлайн» и «Клаустрофобия офлайн»: в каждом 51% у Вадима Змовика, 33% у Павла Вараксина (GrimTeam), 16% у Евгения Авина.',
        'eco.val': 'По экспертной оценке, сеть стоит 400–500 млн ₽.',
    },
    'ce7b84bec': {
        'eco.rationale': 'Деньги от продажи нужны Клячину, чтобы снизить долг, взятый под выкуп активов KR Properties. Эти активы он в этом году выкупил назад у государства; раньше они изымались в счет налоговых претензий по делу нефтекомпании «Русь-ойл».',
        'eco.val': 'Начальная цена лота — 17,1 миллиарда рублей, минимальная — 12,3 миллиарда рублей.',
    },
    'g37737226': {
        'eco.val': 'Если озвученная цена верна, Selectel переплатил: она равна двум годовым выручкам компании. Вероятно, покупателю нужна доля «Единой сети» на рынке выделенных серверов — в 2023 году это третий оператор рынка с долей 10%.',
    },
    'g41075b4e': {
        'eco.rationale': 'Caterpillar остановила завод в Тосно (Ленобласть) в начале марта 2022 из-за санкций и сбоев логистики после начала СВО.',
        'eco.val': 'Оборот лизинговой ООО «Катерпиллар Файненшл» за 2022 — 2 млрд ₽ против 10,3 млрд ₽ в 2021. Ее чистая прибыль снизилась до 153 млн ₽ с 1,5 млрд ₽.',
    },
    'g4e3ec471': {
        'law.struct': 'Куплено 100% долей у закрытого паевого инвестиционного фонда «Азимут-капитал».',
    },
    'g6168731b': {
        'eco.share': 'Около 30 брендов: российские и региональные «Степан Разин», «Три медведя», «Охота» и международные Guinness, Zlaty Bazant, Amstel Premium Pilsener, Heineken.',
        'eco.rationale': 'Компания работала над передачей права собственности на свой бизнес в России и, как того требуют местные правила, подала заявку на одобрение продажи в органы власти РФ. Подробности о покупателе и соглашении она обещала раскрыть, когда получит одобрение.',
    },
    'g656645d5': {
        'seller': 'Cargill',
    },
    'g672c6dfe': {
        'eco.rationale': 'По мнению аналитика, сделка похожа на выход инвестора из проекта — на фоне переориентации потребителей на кофе и травяные напитки.',
    },
    'g6bccb70f': {
        'eco.val': 'По оценкам, итоговая сумма сделки составила около 10,88 млрд ₽ — более чем вдвое меньше первоначальной.',
        'law.struct': 'Стороны пересмотрели порядок расчетов: Fusion Factor Fintech мог рассчитаться с NanduQ двумя частями — 4 млрд ₽ деньгами ($50,3 млн по курсу конца 2025 года) и 29,288 млн акций класса B самой NanduQ. Fusion Factor Fintech Limited — материнский холдинг группы АО «Киви»; его менеджмент решил реорганизовать АО «Киви», и первый этап включает регистрацию новых юрлиц.',
    },
    'g6d711306': {
        'eco.rationale': 'Для современного телекоммуникационного бизнеса владение недвижимостью — неправильная активность, заявили в «Вымпелкоме»: компания предпочитает гибко использовать площади, продавая объекты без операционной необходимости или сдавая их в аренду, а освободившийся капитал направляет на развитие сети, внедрение новых технологий и повышение качества обслуживания клиентов.',
        'eco.val': 'Стартовая цена лота — 1,05 млрд ₽. Торги голландские: цена идет на понижение, но не ниже 735 млн ₽.',
        'law.struct': 'Аукцион организован по голландской схеме — на понижение, с минимальной ценой 735 млн рублей.',
    },
    'g88d5e740': {
        'eco.target_fin': 'Мощности: Ревда — 2,2 млн т заготовки в год, Нижние Серги — 1 млн т/год, «НЛМК-Метиз» — 560 тыс. т/год. Выручка «НЛМК-Урал» в 2022 году — 76 млрд ₽ (снижение с 95 млрд ₽ годом ранее), чистая прибыль — 4,7 млрд ₽ (снижение с 15,9 млрд ₽).',
        'law.appr': 'ФАС одобрила сделку 21 сентября 2023 года с условиями: покупатель обязан исполнить все договоры поставки, действующие на дату сделки, в течение трех месяцев представить в ФАС принципы взаимодействия с потребителями, а через полгода — ежемесячно продавать на бирже не менее 5% арматуры от месячного объема производства.',
    },
    'g8de46135': {
        'eco.rationale': 'По неофициальным данным, топ-менеджеры Faurecia в России собираются выкупить активы французской группы и запустить их заново. Для этого в конце июня они учредили «Формат Инвест».',
        'law.struct': 'В сентябре Горин вышел из компании, а остальные совладельцы, кроме Татьяны Громовой и Оливье Гриненберже, получили по 7,5%. Оливье Гриненберже в 2023 году получил российский паспорт. Эти 7,5% получили Николай Афанасьев, Марина Давыденко, Евгения Бурцева и Илья Панин. Предметом сделки выступили три юрлица — ООО «Форесия Экологичные решения», ООО «Форесия Автомобильные решения» и АО «Форесия Интериор Тольятти» — они перешли образованному топ-менеджерами ООО «Формат Инвест».',
    },
    'ga1935680': {
        'law.struct': 'Не исключено, что покупка разбита на два этапа. На первом пакет переходит почти даром, и новый владелец старается сделать сеть прибыльной; за второй пакет платят реальные деньги, а сумма привязана к будущим результатам. При такой схеме продавец получает основные деньги не сразу, а позже. Сейчас у сети отрицательная EBITDA и нет прибыли.',
    },
    'gb2d5da8c': {
        'eco.val': 'По неофициальным данным, доля перешла либо по номиналу, либо без оплаты.',
        'eco.target_fin': '«Азот» — один из крупнейших химических холдингов России. За 2025 год его выручка выросла на 5,8%, до 121,9 млрд ₽. Чистая прибыль при этом упала более чем втрое: 4,5 млрд ₽ против 15,5 млрд ₽ в 2024 году. Эти цифры стали известны в июле 2026 года.',
        'law.struct': 'Из капитала ГК «Азот» вышла Светлана Рыбальченко, владевшая 40%: она сестра Михаила Федяева, основателя холдинга «Сибирский деловой союз» (СДС).',
    },
    'gc6322659': {
        'eco.rationale': 'Актив достался не VK, как предполагалось, а структурам кипрского бизнесмена Павла Харанеки (Broadsmart Group); сделка вместе с сервисом Donation Alerts закрылась в декабре 2024 года. По словам продавца, решение позволит My.Games сосредоточиться на приоритетном бизнесе — разработке и издании игр.',
        'eco.val': 'Инвестиционный консультант «Финама» Тимур Нигматуллин оценивает Boosty не менее чем в $10 млн. Аналитик ФГ «Финам» Леонид Делицын оценивает актив в $4–5 млн',
    },
    'gd95bf2d7': {
        'buyer_name': 'Государство (Росимущество, по иску Генпрокуратуры)',
    },
}

# Консультанты дубля, когда у выжившей в «Юристе» стоит только «не раскрывались».
ADV_TRANSFERS = {
    'ccdd90216': [['Юридический консультант', 'LEVEL Legal Services',
                   'LEVEL Legal Services — за продавца; включала внутригрупповую реструктуризацию']],
    'g4e3ec471': [['Юридический консультант ООО «Сбербанк Инвестиции»', 'Orion',
                   'Приобретение 100% ООО «СДМ ТК-2» и продажа 50% ООО «Логопарк 7». Источник: orion-law.com']],
}


# Темы дубля, которых нет у выжившей («Банкротство / долги» у Caterpillar не
# переносится — ни одна из двух карточек не о долгах). Faurecia: обе карточки
# без темы, хотя это уход французской группы из России — тема ставится, иначе
# ассистент не находит сделку по «опциону на обратный выкуп»
# (test_reverse_buyback_option_finds_the_foreign_exits).
THEME_TRANSFERS = {
    'g6168731b': ['Уход иностранного владельца'],
    'gb2d5da8c': ['Консолидация доли'],
    'g8de46135': ['Уход иностранного владельца'],
}


def adv_is_generic(adv) -> bool:
    return not adv or all(isinstance(r, list) and 'не раскрыва' in ' '.join(map(str, r)).lower() for r in adv)


def _fixes_ids(path: Path) -> set[str]:
    """Все id записей FIXES в файле (по AST, как `fixes_entries`)."""
    import ast
    ids = set()
    for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'FIXES' for t in node.targets) \
                and isinstance(node.value, ast.List):
            for el in node.value.elts:
                pairs = el.keywords if isinstance(el, ast.Call) else \
                    [type('kw', (), {'arg': k.value, 'value': v})() for k, v in zip(el.keys, el.values)
                     if isinstance(k, ast.Constant)] if isinstance(el, ast.Dict) else []
                for kw in pairs:
                    if kw.arg == 'id' and isinstance(kw.value, ast.Constant):
                        ids.add(kw.value.value)
    return ids


def remove_empty_written_files(drop_ids: set[str], write: bool) -> list[Path]:
    """Файл `written_<id>_*.py` держит текст одной карточки; когда все его
    записи сняты вместе с карточкой, в файле не остается `FIXES`, и
    `review.py` упал бы на импорте (`module.FIXES`). Такой файл удаляется
    целиком — до снятия записей (сухой прогон) это файл, все id которого
    среди удаляемых; после — файл без `FIXES`."""
    gone = []
    for drop in sorted(drop_ids):
        for path in sorted(mdb.FIXES_DIR.glob(f'written_{drop}_*.py')):
            ids = _fixes_ids(path)
            if ids and not ids <= drop_ids:
                continue
            gone.append(path)
            print(f'FIXES {path.name}: записей не остается — файл удаляется')
            if write:
                path.unlink()
    return gone


def load() -> dict:
    return json.load(open(DATA, encoding='utf-8'))


def drop_to_keep() -> dict:
    return {p['drop']: p['keep'] for p in PAIRS if p['kind'] in ('merge', 'stage', 'drop_only')}


def run(data: dict, write: bool) -> list[str]:
    """Применяет таблицу к `data`. Возвращает список отказов (пустой — все прошло)."""
    errors: list[str] = []
    by_id = {d['id']: d for d in data['deals']}
    remap = drop_to_keep()
    known_ind = mdb.industries()
    known_themes = {t for d in data['deals'] for t in (d.get('themes') or [])}
    merges: list[tuple[dict, mdb.Merge]] = []

    # 1. Слияния и этапы — общим скриптом.
    for p in PAIRS:
        if p['kind'] not in ('merge', 'stage'):
            continue
        spec = dict(p['spec'], keep=p['keep'], drop=p['drop'])
        spec['set'] = {**FIELD_TRANSFERS.get(p['drop'], {}), **(spec.get('set') or {})}
        spec['add_themes'] = sorted(set(spec.get('add_themes') or []) | set(THEME_TRANSFERS.get(p['drop'], [])))
        m = mdb.Merge(data, spec, known_ind, known_themes)
        m.check()
        if p['drop'] in ADV_TRANSFERS:
            keep_adv = ((by_id.get(p['keep']) or {}).get('law') or {}).get('adv')
            if adv_is_generic(keep_adv):
                print(f"  law.adv <- {ADV_TRANSFERS[p['drop']][0][1]}")
            else:
                errors.append(f"#{p['n']}: law.adv у {p['keep']} уже заполнен: {keep_adv}")
        print(f"\n#{p['n']} {p['kind']}: {p['drop']} -> {p['keep']}  ({spec['reason'][:100]}…)")
        for line in m.plan:
            print(line)
        for e in m.errors:
            print('  ОТКАЗ:', e)
        errors.extend(m.errors)
        if p.get('stage'):
            keep = by_id.get(p['keep']) or {}
            kind, date = p['stage'].split('-', 1)
            have = {(e.get('kind'), e.get('date')) for e in (keep.get('events') or [])}
            planned = {(e['kind'], e['date']) for e in (spec.get('events') or [])}
            if (kind, date) not in have | planned:
                errors.append(f"#{p['n']}: этап {p['stage']} не найден ни в карточке, ни в спецификации")
            else:
                print(f"  merged_deal_stages[{p['drop']}] = {p['stage']}")
        for field, (old, new) in (p.get('after') or {}).items():
            cur = (by_id.get(p['keep']) or {}).get(field)
            if cur != old:
                errors.append(f"#{p['n']}: {field} у {p['keep']} = {cur!r}, ожидалось {old!r}")
            else:
                print(f'  {field}: {old!r} -> {new!r}')
        merges.append((p, m))

    # 2. Карточка, уже слитая в merged, но оставшаяся в deals.
    for p in PAIRS:
        if p['kind'] != 'drop_only':
            continue
        print(f"\n#{p['n']} drop_only: {p['drop']} (merged -> {data['merged'].get(p['drop'])})")
        if data['merged'].get(p['drop']) != p['keep']:
            errors.append(f"#{p['n']}: merged[{p['drop']}] != {p['keep']}")
        if p['drop'] not in by_id or p['keep'] not in by_id:
            errors.append(f"#{p['n']}: нет карточки {p['drop']} или {p['keep']}")
        else:
            for field, value in FIELD_TRANSFERS.get(p['drop'], {}).items():
                if not mdb.is_empty(mdb.get_field(by_id[p['keep']], field)):
                    errors.append(f"#{p['n']}: {field} у {p['keep']} уже заполнено")
                elif mdb.get_field(by_id[p['drop']], field) != value:
                    errors.append(f"#{p['n']}: {field} у {p['drop']} не совпадает с таблицей")
                else:
                    print(f'  {field} <- {value[:70]!r}')
            have = mdb.src_urls(by_id[p['keep']])
            missing = [s for s in (by_id[p['drop']].get('src') or []) if s[1] not in have]
            if missing:
                print(f'  src += {len(missing)}')
            if data.get('telegram_posts', {}).get(p['drop']) is not None and p['keep'] in data.get('telegram_posts', {}):
                errors.append(f"#{p['n']}: у обеих карточек посты")

    # 3. Разные сделки: метка и связь.
    separate: list[tuple[dict, str, str]] = []
    for p in PAIRS:
        if p['kind'] != 'separate':
            continue
        a, b = remap.get(p['a'], p['a']), remap.get(p['b'], p['b'])
        if a == b:
            print(f"\n#{p['n']} separate: {p['a']} ⇄ {p['b']} — одна из карточек слита в другую, метка не нужна")
            continue
        for i in (a, b):
            if i not in by_id:
                errors.append(f"#{p['n']}: нет карточки {i}")
        print(f"\n#{p['n']} separate{' + related' if p.get('related') else ''}: {a} ⇄ {b} — {p['why']}")
        separate.append((p, a, b))

    for p in PAIRS:
        if p['kind'] == 'question':
            print(f"\n#{p['n']} ВОПРОС ВЛАДЕЛЬЦУ: {p['a']} ⇄ {p['b']} — {p['why']}")

    # 4. FIXES на удаляемые id.
    drop_ids = set(remap)
    print()
    fixes_removed = mdb.strip_fixes(drop_ids, write=False)
    remove_empty_written_files(drop_ids, write=False)

    # 5. signals.json: ссылка на сделку переезжает на выжившую карточку.
    signals = json.load(open(SIGNALS, encoding='utf-8')) if SIGNALS.exists() else None
    sig_moves = [(r['deal_id'], remap[r['deal_id']]) for r in (signals or {}).get('signals', [])
                 if r.get('deal_id') in remap]
    for old, new in sig_moves:
        print(f'signals.json: deal_id {old} -> {new}')

    n_merge = sum(1 for p in PAIRS if p['kind'] == 'merge')
    n_stage = sum(1 for p in PAIRS if p['kind'] == 'stage')
    n_drop = sum(1 for p in PAIRS if p['kind'] == 'drop_only')
    n_q = sum(1 for p in PAIRS if p['kind'] == 'question')
    print(f'\nПар: {len(PAIRS)}. Дублей слить: {n_merge + n_drop} (из них уже в merged: {n_drop}), этапов: {n_stage}, '
          f'разных сделок: {len(separate)} (связать: {sum(1 for p, _, _ in separate if p.get("related"))}), '
          f'вопросов владельцу: {n_q}. Сделок {len(data["deals"])} -> {len(data["deals"]) - len(drop_ids)}, '
          f'записей FIXES снять: {fixes_removed}')
    if errors or not write:
        return errors

    # ---- Запись ----
    before = len(data['deals'])
    for p, m in merges:
        m.apply()
        keep = next(d for d in data['deals'] if d['id'] == p['keep'])
        if p.get('stage'):
            for e in keep.get('events') or []:
                if f"{e.get('kind')}-{e.get('date')}" == p['stage'] and not e.get('id'):
                    e['id'] = p['stage']
            assert any(e.get('id') == p['stage'] for e in keep['events']), p['n']
            data.setdefault('merged_deal_stages', {})[p['drop']] = p['stage']
        for field, (old, new) in (p.get('after') or {}).items():
            assert keep.get(field) == old, (p['n'], field, keep.get(field))
            keep[field] = new
        if p['drop'] in ADV_TRANSFERS:
            assert adv_is_generic((keep.get('law') or {}).get('adv')), p['n']
            keep.setdefault('law', {})['adv'] = ADV_TRANSFERS[p['drop']]
    for p in PAIRS:
        if p['kind'] != 'drop_only':
            continue
        keep = next(d for d in data['deals'] if d['id'] == p['keep'])
        drop = next(d for d in data['deals'] if d['id'] == p['drop'])
        have = mdb.src_urls(keep)
        keep.setdefault('src', []).extend(s for s in (drop.get('src') or []) if s[1] not in have)
        for field, value in FIELD_TRANSFERS.get(p['drop'], {}).items():
            assert mdb.is_empty(mdb.get_field(keep, field)) and mdb.get_field(drop, field) == value, (p['n'], field)
            mdb.put_field(keep, field, value)
        posts = data.setdefault('telegram_posts', {})
        if p['drop'] in posts:
            mid = posts.pop(p['drop'])
            if mid is not None or p['keep'] not in posts:
                posts[p['keep']] = mid
        assert data['merged'][p['drop']] == p['keep']
        data['deals'] = [d for d in data['deals'] if d['id'] != p['drop']]
    assert len(data['deals']) == before - len(drop_ids), (len(data['deals']), before, len(drop_ids))
    ids = {d['id'] for d in data['deals']}
    assert not drop_ids & ids
    for p, a, b in separate:
        ca = next(d for d in data['deals'] if d['id'] == a)
        cb = next(d for d in data['deals'] if d['id'] == b)
        for c in (ca, cb):
            c['separate_transaction_reviewed'] = True  # метка может уже стоять от соседней пары
        if p.get('related'):
            ca['related_deal_ids'] = sorted(set((ca.get('related_deal_ids') or []) + [b]))
            cb['related_deal_ids'] = sorted(set((cb.get('related_deal_ids') or []) + [a]))
    for d in data['deals']:
        for r in d.get('related_deal_ids') or []:
            assert r in ids, (d['id'], r)
    mdb.strip_fixes(drop_ids, write=True)
    remove_empty_written_files(drop_ids, write=True)
    if signals and sig_moves:
        for r in signals['signals']:
            if r.get('deal_id') in remap:
                r['deal_id'] = remap[r['deal_id']]
        json.dump(signals, open(SIGNALS, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    errors = run(load(), write=False)
    if errors:
        print(f'\nОТКАЗОВ: {len(errors)} — ничего не записано.')
        return 1
    if not args.write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0
    # База перечитывается прямо перед записью: за время сухого прогона ее мог изменить другой прогон.
    errors = run(load(), write=True)
    if errors:
        print(f'\nОТКАЗОВ при записи: {len(errors)} — ничего не записано.')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
