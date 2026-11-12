# -*- coding: utf-8 -*-
"""Разовая часть вычитки 12 ноября 2026 (марафон, партия m052), часть 2: то, что не ложится в таблицу FIXES.

- суммы: gf87a65f7 «$7–7,5 млрд» — оценка компании собеседниками Bloomberg, сделка не состоялась; g4bb21315
  «3–7,9 млрд ₽ (по оценке)» — оценки аналитиков; g85b8634d «≈360 млн ₽» — выручка NovaScreen за 2021 год, а не цена
  (review.py не принимает «Не раскрыта» и «≈»); g8b9d2708 — одна цена в двух полях одинаково;
- даты: gf87a65f7 — 22.05.2023 неделя заседания совета, срыв сделки без дня — год; g85b8634d — 27.04.2023 день
  статьи — год; g221e4969, ga06c75e2, g531446fe — дата совпадает с ЕГРЮЛ, ставится основание;
- стороны (издания из списка нежелательных — The Moscow Times, Meduza, «Медиазона» — в источники не берутся): продавец g221e4969 по ЕГРЮЛ — ООО «Бонум Инвестментс» (ИНН 7706417487), а не ООО «Бонум Кэпитал»; продавец
  g85b8634d по Vademecum — «МедИнвестГрупп» (ООО «МИГ», ИНН 9729102215, учредитель АО «Биоскрин»), а «Огмент
  инвестментс лимитед» не подтвердился; предмет g531446fe — ООО «СиЭнЭйч Индастриал Руссия» (ИНН 1650202670: СПАРК,
  fabricators.ru, b2b-center) — профиля не было;
- структура по реестру (g7b2a78bf), предмет-доля ga06c75e2, отрасль ga06c75e2 (управляющая компания), источники;
- профили: описания без пересказа сделки и оценок, правовая форма.

    python3 pipeline/archive/2026-11/reread_oneoff_m052b.py           # сухо
    python3 pipeline/archive/2026-11/reread_oneoff_m052b.py --write   # запись; повторный запуск — «уже применено»
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import fact_edit_guard  # noqa: E402
import fns_registry  # noqa: E402
import accept_card  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
REG = os.path.join(ROOT, 'pipeline', 'fns_registry.py')
BY = 'reread_oneoff_m052b (вычитка 12.11.2026)'
DAY = '2026-11-12'
_REG = 'https://projectcompass.ru/api/companies/%s/fns'

_GU_STRUCT_OLD = ('Пут-опцион заключили в конце 2015 года: Guess обязан был выкупить 30% партнера до 31 декабря 2025 года, '
                  'если тот решит их продать.')
_GU_STRUCT = ('В конце 2015 года стороны заключили пут-опцион: Шикулов мог продать свои 30%, а Guess обязалась выкупить '
              'их до 31 декабря 2025 года. Шикулов исполнил опцион досрочно, в ноябре 2022 года. По ЕГРЮЛ, 22 мая 2023 '
              'года его 30% перешли к Guess Europe Sagl, а 100% «Гесс Сиайэс» оказались у структур Guess.')

_PM_Q = ('ЕГРЮЛ ООО «Паскаль медикал» (ИНН 7705243630): 2023-05-19 ООО «БОНУМ ИНВЕСТМЕНТС» вышло из состава участников '
         '(49%), Сарманов Максим Николаевич вошел (49%). — Ведомости: «Бонум инвестментс» Мурата Алиева … передала 49% '
         'долей в компании «Паскаль медикал» … гендиректору предприятия Максиму Сарманову.')
_NV_Q = ('Vademecum: NovaScreen принадлежала «МедИнвестГрупп» Виктора Харитонина и насчитывала 55 медицинских офисов. — '
         'ЕГРЮЛ АО «Биоскрин» (ИНН 9709033725, юрлицо NovaScreen): учредитель — ООО «МИГ» (ИНН 9729102215, ОГРН '
         '1177746645933; полное имя — ООО «МедИнвестГрупп»).')
_CN_Q = ('Интерфакс: Новым владельцем российского представительства … CNH Industrial - ООО "СиЭнЭйч Индастриал Руссия" - '
         'стала компания его гендиректора Михаила Мураховского, следует из данных ЕГРЮЛ.')
_BS_Q = ('ЕГРЮЛ ООО «УК «А-Капитал»» (ИНН 7707583543): 2023-04-28 ПАО «БАНК «САНКТ-ПЕТЕРБУРГ» вышло из состава '
         'участников (100%), ПАО БАНК «АЛЕКСАНДРОВСКИЙ» вошло (100%). — Ъ: О том, что банк «Санкт-Петербург» продал '
         'управляющую компанию «БСПБ Капитал», стало известно из данных ЕГРЮЛ.')

# Новые профили: ключ — метка, id выбирается accept_card._new_profile_id
_NEW = {
    'bonum_inv': {'name': 'Бонум Инвестментс', 'legal_short': 'ООО «Бонум Инвестментс»', 'ind': 'Управление активами',
                  'desc': ('Инвестиционная компания группы Bonum Capital Мурата Алиева; с конца 2022 года под санкциями '
                           'США.'),
                  'keys': ['бонум инвестментс', 'бонум инвестментс ооо'], 'inn': '7706417487',
                  'reason': ('ООО «Бонум Инвестментс» ИНН 7706417487, ОГРН 1157746124656, учреждено 20.02.2015: '
                             'OpenSanctions (выгрузка ЕГРЮЛ ru-inn-7706417487; OFAC SDN; реестр санкций СНБО Украины); '
                             'то же лицо — участник ООО «Паскаль медикал» с 49% до 19.05.2023 по истории участников на '
                             'сайте (/fns) и в OpenSanctions.')},
    'mig': {'name': 'МедИнвестГрупп', 'legal_short': 'ООО «МедИнвестГрупп»', 'ind': 'Здравоохранение',
            'desc': ('Инвестиционный холдинг в здравоохранении (сокращенное имя юрлица — ООО «МИГ»), принадлежит '
                     'Виктору Харитонину.'),
            'keys': ['мединвестгрупп', 'миг медицина'], 'inn': '9729102215',
            'reason': ('ООО «МедИнвестГрупп» (ООО «МИГ») ИНН 9729102215, ОГРН 1177746645933 — учредитель АО «Биоскрин» '
                       '(юрлицо NovaScreen) по ЕГРЮЛ на сайте (/fns); tapki.com и Циклопедия: ООО «МедИнвестГрупп», '
                       'краткое имя ООО «МИГ», зарегистрировано в Москве в июле 2017 года — совпадает с ОГРН 117…; '
                       'Vademecum: NovaScreen принадлежала «МедИнвестГрупп» Виктора Харитонина.')},
    'cnh_rus': {'name': 'СиЭнЭйч Индастриал Руссия', 'legal_short': 'ООО «СиЭнЭйч Индастриал Руссия»',
                'ind': 'Машиностроение',
                'desc': ('Бывшая российская «дочка» CNH Industrial (сельхозтехника Case IH и New Holland, строительная '
                         'техника); с 2023 года принадлежит ООО «Юнайтед Индастриал Дистрибушен».'),
                'keys': ['сиэнэйч индастриал руссия'], 'inn': '1650202670',
                'reason': ('ООО «СиЭнЭйч Индастриал Руссия» ИНН 1650202670, ОГРН 1101650000870, Набережные Челны: '
                           'СПАРК-Интерфакс (карточка ooo-sieneich-indastrial-russiya-inn-1650202670), fabricators.ru '
                           '(ОГРН 1101650000870, КПП 165001001), b2b-center; Интерфакс 898224 — то же юрлицо перешло под '
                           'контроль ООО «Юнайтед Индастриал Дистрибушен» 25.04.2023.')},
}
# (id карточки, поле, метка нового профиля, старое значение, цитата, адрес)
_LINK = [
    ('g221e4969', 'seller_id', 'bonum_inv', 'g829090b3', _PM_Q, _REG % 'g99120dbb'),
    ('g85b8634d', 'seller_id', 'mig', 'g1356353d', _NV_Q, 'https://vademec.ru/news/2023/04/27/medskan-priobrel-laboratorii-novascreen/'),
    ('g531446fe', 'target', 'cnh_rus', None, _CN_Q, 'https://www.interfax.ru/business/898224'),
]

_SET = [
    ('g7b2a78bf', 'law.struct', _GU_STRUCT_OLD, _GU_STRUCT, None, None),
    ('g7b2a78bf', 'eco.share', '30% ООО «Гесс? Сиайэс», выкупленные у Вячеслава Шикулова; после сделки доля структур '
     'Guess? Inc. выросла до 100%.', '30% долей ООО «Гесс Сиайэс»',
     'Структуры американского производителя и продавца одежды Guess? Inc. консолидировали 100% ООО «Гесс? Сиайэс», '
     'выкупив 30% в компании у предпринимателя Вячеслава Шикулова.', 'https://www.kommersant.ru/doc/6001381'),
    ('gf87a65f7', 'sum', '$7–7,5 млрд', 'Не раскрыта',
     'Компанию оценили в 560-600 млрд рублей — это $7-7,5 млрд, говорят собеседники издания. (оценка по заявкам; '
     'сделка не состоялась, цена не согласована)', 'https://vc.ru/money/699432-niderlandskaya-yandex-n-v-poluchila-zayavki-na-pokupku-51-yandeksa-za-7-mlrd-bloomberg'),
    ('gf87a65f7', 'eco.sum', '$7–7,5 млрд', 'Не раскрыта',
     'Компанию оценили в 560-600 млрд рублей — это $7-7,5 млрд, говорят собеседники издания. (оценка, не цена)',
     'https://vc.ru/money/699432-niderlandskaya-yandex-n-v-poluchila-zayavki-na-pokupku-51-yandeksa-za-7-mlrd-bloomberg'),
    ('gf87a65f7', 'date', '2023-05-22', '2023',
     'Продажа «Яндекса» консорциуму российских инвесторов «забуксовала» из-за бизнесменов под санкциями … одобренный '
     'Путиным консорциум не устраивает иностранных директоров в совете. (VC.ru, 23.06.2023; 22.05.2023 — неделя '
     'заседания совета, дня срыва в источниках нет)',
     'https://vc.ru/money/736941'),
    ('g221e4969', 'seller', 'Bonum Capital', 'Бонум Инвестментс', _PM_Q, _REG % 'g99120dbb'),
    ('g221e4969', 'date_basis', None, 'registry', None, None),
    ('g4bb21315', 'sum', '3–7,9 млрд ₽ (по оценке)', 'Не раскрыта',
     'Гендиректор "Infoline-аналитики" Михаил Бурмистров считает, что покупка могла обойтись АФК "Система" не более чем '
     'в 3 млрд рублей . Но сумма сделки все же официально не раскрывается.',
     'https://oborot.ru/news/osnovnoj-akcioner-ozona-kupil-natura-siberica-skolko-eto-moglo-stoit-i185102.html'),
    ('g4bb21315', 'eco.sum', '3–7,9 млрд ₽ (по оценке)', 'Не раскрыта',
     'Но сумма сделки все же официально не раскрывается.',
     'https://oborot.ru/news/osnovnoj-akcioner-ozona-kupil-natura-siberica-skolko-eto-moglo-stoit-i185102.html'),
    ('g8b9d2708', 'sum', '800 млн $', '$800 млн',
     'Russell … announced back in May plans to buy an 82% stake in Forbes Global Media Holdings in a deal that values '
     'the company at nearly $800 million.',
     'https://techcrunch.com/2023/11/21/tech-ceo-austin-russells-bid-to-buy-forbes-fails/'),
    ('ga06c75e2', 'date_basis', None, 'registry', None, None),
    ('ga06c75e2', 'eco.share', '—', '100% долей ООО «УК «БСПБ Капитал»» (теперь ООО «УК «А-Капитал»»)', _BS_Q,
     _REG % 'gbspbcapital'),
    ('ga06c75e2', 'ind', 'Рынок ценных бумаг', 'Управление активами', None, None),
    ('g85b8634d', 'sum', '≈360 млн ₽ (по оценке)', 'Не раскрыта',
     'Подробности сделки в сообщении не раскрываются, стороны о них не рассказывают. … По итогам 2021 года сеть заняла '
     '36-е место … с выручкой 360 млн рублей. (360 млн ₽ — выручка, не цена)',
     'https://vademec.ru/news/2023/04/27/medskan-priobrel-laboratorii-novascreen/'),
    ('g85b8634d', 'eco.sum', '≈360 млн ₽ (по оценке)', 'Не раскрыта',
     'Подробности сделки в сообщении не раскрываются, стороны о них не рассказывают.',
     'https://vademec.ru/news/2023/04/27/medskan-priobrel-laboratorii-novascreen/'),
    ('g85b8634d', 'date', '2023-04-27', '2023',
     'Лаборатории NovaScreen стали частью сети KDL группы «Медскан», говорится на сайте NovaScreen. (27.04.2023 — день '
     'статьи; по Ведомостям, юридически сделка на тот день не закрыта, дня закрытия в источниках нет)',
     'https://vademec.ru/news/2023/04/27/medskan-priobrel-laboratorii-novascreen/'),
    ('g85b8634d', 'seller', '«Огмент инвестментс лимитед» (владельцы — Виктор Харитонин и Егор Кульков)',
     'ООО «МедИнвестГрупп»', _NV_Q, 'https://vademec.ru/news/2023/04/27/medskan-priobrel-laboratorii-novascreen/'),
    ('g531446fe', 'date_basis', None, 'registry', None, None),
]

_ADD_SRC = {
    'gf87a65f7': [['Ведомости', 'https://www.vedomosti.ru/business/news/2023/05/25/976926-yandeks-podtverdil'],
                  ['VC.ru', 'https://vc.ru/money/736941'],
                  ['BFM.ru', 'https://www.bfm.ru/news/528212'],
                  ['Деловой Петербург', 'https://www.dp.ru/a/2024/07/15/jandeks-stal-okonchatelno']],
    'g221e4969': [],
    'g8b9d2708': [['Spokesman-Review (The Washington Post)', 'https://www.spokesman.com/stories/2023/oct/20/russian-tycoon-claims-he-is-behind-forbes-purchase/'],
                  ['Talking Biz News', 'https://talkingbiznews.com/media-news/koch-pe-arm-looking-to-bid-for-forbes/']],
    'ga06c75e2': [['Деловой Петербург', 'https://www.dp.ru/a/2024/11/11/upravljajushhuju-kompaniju-peterburgskogo'],
                  ['Деловой Петербург', 'https://www.dp.ru/a/2025/04/09/uk-akapital-obnovila-strukturu']],
}

_PROFILE = [
    ('g3b9d27f8', 'desc', 'Российский бизнес Guess; в 2023 году Guess выкупил у партнера Вячеслава Шикулова его 30% '
     'доли по пут-опциону 2015 года, разрешение OFAC получено до закрытия.',
     'Управляет сетью магазинов Guess в России: на конец 2025 года — 46 точек.'),
    ('g46a02673', 'desc', 'Гендиректор ООО «Паскаль медикал»; в 2023 году купил у Bonum Capital 49% долей компании — '
     'номинальная сделка для защиты предприятия от санкционных рисков после включения инвестора в санкционный список США.',
     'Гендиректор ООО «Паскаль медикал» и совладелец компании.'),
    ('g99120dbb', 'desc', 'Производитель медицинских изделий, резидент ОЭЗ «Дубна»; в 2023 году из капитала (49% долей) '
     'вышла Bonum Capital — сделка, по оценке экспертов, номинальная, для защиты компании от санкционных рисков.',
     'Производитель одноразовых шприцев и игл в ОЭЗ «Дубна» (Московская область), выпускает их с 2018 года.'),
    ('gabe80712', 'desc', 'В 2023 году купил у Банка «Санкт-Петербург» управляющую компанию «БСПБ Капитал» (активы под '
     'управлением 17,8 млрд ₽ на конец 2021 года).',
     'Универсальный банк из Санкт-Петербурга; основные акционеры — Евгений Лотвинов и Игорь Лейтис.'),
    ('gabe80712', 'ind', 'Рынок ценных бумаг', 'Банки'),
    ('gbspbcapital', 'desc', 'Управляющая компания: доверительное управление активами и инвестиционное консультирование. '
     'До 2025 года входила в группу банка «Санкт-Петербург».',
     'Управляющая компания: паевые фонды, доверительное управление, инвестиционное консультирование. До 2023 года '
     'входила в группу банка «Санкт-Петербург», теперь называется «А-Капитал».'),
    ('gbspbcapital', 'ind', 'Банки', 'Управление активами'),
    ('g9352b17b', 'name', 'лаборатории NovaScreen', 'NovaScreen'),
    ('g9352b17b', 'desc', 'Сеть из 55 медицинских лабораторий в Москве; в 2023 году ее купил «Медскан» у связанной с '
     '«Фармстандартом» «Огмент инвестментс лимитед», переоткрыв точки под брендом KDL.',
     'Сеть из 55 медицинских лабораторий в Москве (юрлицо — АО «Биоскрин»); с 2023 года ее точки работают под брендом '
     'KDL.'),
    ('g16606d0d', 'desc', 'Российский бизнес CNH Industrial по производству сельхозтехники; в 2023 году его 99% купил '
     'Михаил Мураховский, бывший бизнес-директор CNH Industrial в России и Белоруссии.',
     'Дистрибьютор сельхозтехники Case IH, New Holland и McCormick в России; зарегистрирован в Москве в декабре 2022 '
     'года, 99% принадлежит Михаилу Мураховскому.'),
]

_LEGAL = [('g3b9d27f8', 'ООО «Гесс Сиайэс»'), ('gdfb1ba6e', 'ООО «Натура Сиберика»'),
          ('gabe80712', 'ПАО Банк «Александровский»'), ('gbspbcapital', 'ООО «УК «А-Капитал»»'),
          ('gf881a88f', 'ПАО «Банк «Санкт-Петербург»»'), ('g9352b17b', 'АО «Биоскрин»'),
          ('g1356353d', 'МКООО «Огмент Инвестментс Лимитед»'), ('g16606d0d', 'ООО «Юнайтед Индастриал Дистрибушен»'),
          ('g829090b3', 'ООО «Бонум Кэпитал»')]

_INN = []

_NOTES = {
    'g7b2a78bf': {'no_profile': {'seller': (
        'Продавец — физическое лицо Вячеслав Шикулов (по ЕГРЮЛ вышел 22.05.2023 с 30%); профили людей не заводятся.')}},
    'gf87a65f7': {'no_profile': {'buyer': (
        'Претенденты — Владимир Потанин и Вагит Алекперов (заявки отдельно; в консорциум Потанина могли войти ВТБ и '
        'Алексей Мордашов); сделка с ними не состоялась, итоговый покупатель — ЗПИФ «Консорциум.Первый» (карточка '
        'gd73fd825).')}},
    'g4bb21315': {'no_profile': {'seller': (
        'АФК купила 100% акций АО «Органик Рус»; акционеров АО реестр не показывает, стороны продавца не назвали. По '
        'ЕГРЮЛ «Натура Сиберика» перешла к АО «Органик Рус» от АО «Корпорация АГ» 26.04.2023 (внутригрупповой шаг). '
        'Искали: Ведомости (2), Oborot.ru, BFM.ru, история участников на сайте (/fns), WebSearch.')}},
    'g8b9d2708': {'no_profile': {'seller': (
        'Integrated Whale Media Investments — гонконгская компания, владелец около 95% Forbes с 2014 года; российского '
        'юрлица нет, профиль не заводился.')}},
}


def _get(card, field):
    o = card
    for p in field.split('.'):
        o = o.get(p) if isinstance(o, dict) else None
    return o


def _set(card, field, value):
    parts = field.split('.')
    o = card
    for p in parts[:-1]:
        o = o.setdefault(p, {})
    o[parts[-1]] = value


def _pid(data, key):
    want = _NEW[key]
    for cid, c in data['companies'].items():
        if c.get('legal_short') == want['legal_short'] and c.get('name') == want['name']:
            return cid
    return None


def apply(data):
    deals = {d['id']: d for d in data['deals']}
    comps = data['companies']
    n = 0
    for key, p in _NEW.items():
        if not _pid(data, key):
            names = {str(c.get('name') or '').lower() for c in comps.values()}
            assert p['name'].lower() not in names, p['name']
            pid = accept_card._new_profile_id(data, p['name'])
            comps[pid] = {'name': p['name'], 'ind': p['ind'], 'desc': p['desc'], 'kpi': [], 'legal_short': p['legal_short']}
            data.setdefault('match_keys', {})[pid] = list(p['keys'])
            n += 1
    for cid, field, key, old, quote, url in _LINK:
        pid = _pid(data, key)
        card = deals[cid]
        if card.get(field) == pid:
            continue
        assert card.get(field) == old, (cid, field, card.get(field))
        card[field] = pid
        fact_edit_guard.log(card, {'seller_id': 'seller'}.get(field, field), pid, quote, url, BY, DAY)
        n += 1
    for cid, rows in _ADD_SRC.items():
        have = {u for _l, u in deals[cid].get('src') or []}
        for row in rows:
            if row[1] not in have:
                deals[cid].setdefault('src', []).append(list(row))
                n += 1
    for cid, field, old, new, quote, url in _SET:
        card = deals[cid]
        cur = _get(card, field)
        if cur == new:
            # значение могло прийти раньше другим шагом записи — цитата у правки факта все равно нужна
            if quote and not fact_edit_guard._backed_by_log(card, field, new):
                fact_edit_guard.log(card, field, new, quote, url, BY, DAY)
                n += 1
            continue
        assert cur == old, (cid, field, cur)
        _set(card, field, new)
        if quote:
            fact_edit_guard.log(card, field, new, quote, url, BY, DAY)
        n += 1
    for pid, field, old, new in _PROFILE:
        c = comps[pid]
        if c.get(field) == new:
            continue
        assert c.get(field) == old, (pid, field, c.get(field))
        c[field] = new
        n += 1
    for pid, short in _LEGAL:
        c = comps[pid]
        if not c.get('legal_short'):                 # party_legal_names.py мог поставить раньше — не спорим
            c['legal_short'] = short
            n += 1
    for cid, notes in _NOTES.items():
        acc = deals[cid].setdefault('accepted_notes', {})
        for k, v in notes.items():
            cur = acc.setdefault(k, {})
            for a, b in v.items():
                if cur.get(a) != b:
                    cur[a] = b
                    n += 1
    return n


def registry_rows(data=None):
    have = fns_registry.by_company_id()
    rows = []
    inn = list(_INN)
    if data is not None:
        for key, p in _NEW.items():
            pid = _pid(data, key)
            if pid:
                inn.append({'company_id': pid, 'decision': 'confirmed', 'inn': p['inn'], 'reason': p['reason'], 'date': DAY})
    for r in inn:
        cur = have.get(r['company_id'])
        if cur and cur.get('inn') == r['inn']:
            continue
        assert not cur or not cur.get('inn'), cur
        assert fns_registry.inn_is_valid(r['inn'])
        assert r['inn'] not in {x.get('inn') for x in fns_registry.REGISTRY if x.get('inn')}
        rows.append(r)
    return rows


def registry_block(rows):
    lines = ['', '', '# Вычитка m052b — %s (pipeline/archive/2026-11/reread_oneoff_m052b.py).' % DAY, 'REGISTRY += [']
    for r in rows:
        lines += ['    {"company_id": %r, "decision": "confirmed", "inn": %r,' % (r['company_id'], r['inn']),
                  '     "reason": %r,' % r['reason'],
                  '     "date": %r},' % r['date']]
    lines.append(']')
    return '\n'.join(lines)


if __name__ == '__main__':
    write = '--write' in sys.argv
    data = json.load(open(DATA, encoding='utf-8'))
    n = apply(data)
    rows = registry_rows(data)
    print('Изменений: %d, новых ИНН: %d' % (n, len(rows)) if (n or rows) else 'Уже применено.')
    if write and (n or rows):
        raw = open(DATA, encoding='utf-8').read()
        data = json.loads(raw)                       # перечитать прямо перед записью
        apply(data)
        rows = registry_rows(data)
        with open(DATA, 'w', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else ''))
        if rows:
            src = open(REG, encoding='utf-8').read()
            marker = "\n\ndef by_company_id() -> dict[str, dict]:"
            assert marker in src
            with open(REG, 'w', encoding='utf-8') as f:
                f.write(src.replace(marker, registry_block(rows) + marker, 1))
        print('Записано.')
    elif not write:
        print('Сухой прогон. Запись — с ключом --write.')
