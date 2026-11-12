# -*- coding: utf-8 -*-
"""Разовая часть вычитки, партия m012 (марафон 12 ноября 2026): стороны, даты, суммы, отрасль, профили.

Что чинит (по статьям и ЕГРЮЛ, тексты — data/inbox/triage/sources_2026-11-12_m012.json; проза и заголовки —
pipeline/ingest/fixes/reread_2026_11_12_m012.py):
  g75920ee3 — продавец ЛУКОЙЛ не был связан; дата — день заявления IHC (21 ноября 2025), а не публикации РБК.
  g9fc75a9c — отрасль: Mixit — косметика («Потребительские товары»), не пищепром; профиль: «IPO на Мосбирже» нет в источниках.
  g84fd8194 — $20–22 млрд — оценка всего портфеля ЛУКОЙЛа, не цена покупки для Chevron: сумма снята; продавец ЛУКОЙЛ.
  g61182014 — продавцы по ЕГРЮЛ: Чадеева вышла из ООО в декабре 2024 года; Novus Capital не подтвердился; профиль покупателя.
  g335d3cdc — дата — день записи в ЕГРЮЛ (11 ноября 2025).
  g3fb43064 — сумма: «около 6 млрд» (6–7 млрд склеивало цену и вложения в стройку); дата — ЕГРЮЛ (7 ноября 2025);
              профиль ООО «Исток» стоял на ИНН АО МЭЗ «Лискинский» (другое юрлицо) — ИНН 3652011018 (ОГРН 1093652000474:
              декларация МЧС и история участников datanewton: Вдовин → Избрехт); Избрехт — бывший вице-президент «Интегры».
  ge56325d9 — дата 1 ноября — заглушка: день сделки неизвестен (ДП: «когда именно прошла сделка… установить невозможно»).
  ga218f75c — 500 млн ₽ — оценка вместе с долгом (Пешков), не цена; покупатель — компания «Акульчев», не человек.
  gbb7e25e1 — сумма: одна оценка без «альтернатив»; отрасль — туризм, не транспорт.
  gd66af0f7, g8af20254 — дата по ЕГРЮЛ (date_basis).

Запуск: без ключа — сухой прогон; --write — запись (база перечитывается прямо перед записью). Повторный запуск
ничего не ломает: примененное пропускается.
"""
import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
sys.path.insert(0, ROOT)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
REG_JSON = os.path.join(ROOT, 'pipeline', 'fns_registry.json')
BY = 'reread m012'
REG = 'https://projectcompass.ru/api/companies/%s/fns'
DN = 'https://datanewton.ru/api/v2/history?ogrn=%s&startDate=2000-01-01&attributes=OWNERS'

Q_IHC = ('"Лукойл" в конце октября заявил, что в связи с введением санкций намерен продать свои зарубежные активы и уже начал '
         'рассматривать предложения от потенциальных покупателей.')
Q_NAT = ("November 21, 2025 Add on Google The UAE's International Holding Company ( IHC ) said on Friday it is exploring "
         "the possibility of purchasing Lukoil 's foreign assets")
Q_MX = 'Их доля в размере 32,98% перешла самой «УК Миксит», управляющей производителем косметики Mixit.'
Q_CH_VAL = 'Там же отметили, что стоимость активов оценивается в 20 миллиардов долларов.'
Q_CH_SELL = ('has said it is seeking buyers for its international assets, which produce 0.5% of global oil and are estimated '
             'to be worth about $22 B, based on 2024 filings.')
Q_YA_REG = ('2025-11-14 left: Мельничук Николай Викторович (61.9014 → None)\n2025-11-14 left: Зайцев-Зотов Андрей Сергеевич '
            '(18.0243 → None)\n2025-11-14 left: Степанов Дмитрий Геннадьевич (3.13411 → None)\n2025-11-14 joined: АО '
            '"НОВЫЙ ИНТЕЛЛЕКТ" (None → 100.0)\n2024-12-25 share_changed: Зайцев-Зотов Андрей Сергеевич (78.0598 → 18.0243)\n'
            '2024-12-25 left: Чадеева Марина Валентиновна (16.9402 → None)')
Q_YA_CONS = 'В «Ясно» сообщили “Ъ”, что покупателем сервиса стал консорциум частных инвесторов. В компании не стали раскрывать подробности сделки.'
Q_MK_REG = '2025-11-11 left: Бредихин Андрей Юрьевич (99.01 → None)\n2025-11-11 joined: ООО "ТОРГОВЫЙ ДОМ ММК" (None → 100.0)'
Q_IS_SUM = 'Сумма сделки могла составить около 6 млрд рублей.'
Q_IS_REG = ('2025-11-07: было — ВДОВИН РУСЛАН ВЯЧЕСЛАВОВИЧ (ИНН: 361403141411) 100.0%; (10 000 руб.); стало — нет\n'
            '2025-11-07: было — нет; стало — ИЗБРЕХТ ДЕНИС ВИКТОРОВИЧ (ИНН: 680399880254) 100.0%; (10 000 руб.)')
Q_IS_AKM = ('Вместе с основной производственной компанией «Исток» была продана Д.Избрехту транспортная компания ООО '
            '«Исток-Логистик».')
Q_GP = 'Соответственно, когда именно прошла сделка, кто и в каких долях владеет активом, установить невозможно.'
Q_KO_PESH = 'Руководитель департамента M&A BGP Capital Иван Пешков полагает, что сумма сделки с учетом долга могла составить 500 млн руб.'
Q_FS = ('Стоимость сделки составляет около 15–16 млрд руб. (около $200 млн), рассказал газете «Известия» совладелец крупного '
        'туроператора, знакомый с параметрами соглашения.')
Q_FS_IND = ('Объединенная компания Wildberries & Russ (ООО «РВБ») приобрела одного из лидеров российской туриндустрии Fun&Sun у '
            'структур «Севергрупп» Алексея Мордашова.')

RIA = 'https://ria.ru/20251122/sanktsii-2056808398.html'
NAT = 'https://www.thenationalnews.com/business/energy/2025/11/21/ihc-interested-in-lukoils-foreign-assets-talking-with-us-treasury'
VED_MX = 'https://www.vedomosti.ru/business/articles/2025/11/20/1156456-vim-investitsii-vishli-iz-kapitala-proizvoditelya-kosmetiki-mixit'
URA = 'https://ura.news/news/1053036396'
HP = 'https://hydrocarbonprocessing.com/news/2025/11/chevron-joins-race-to-explore-potential-purchase-of-lukoil-assets/'
KOM_YA = 'https://www.kommersant.ru/doc/8212273'
ABIREG = 'https://abireg.ru/newsitem/110293/'
AKM_IS = 'https://www.akm.ru/news/masloekstraktsionnyy_zavod_istok_v_voronezhskikh_liskakh_prodan_d_izbrekhtu/'
DP = 'https://www.dp.ru/a/2025/11/13/trc-zhemchuzhnaja-plaza-pereshjol'
KOM_KO = 'https://www.kommersant.ru/doc/8293536'
KOM_FS = 'https://www.kommersant.ru/doc/8140246'

LUKOIL = 'g5c8c6494'

# (карточка, поле, старое значение, новое, цитата, адрес) — факты, с fact_edit_guard.log
ONE_OFF = [
    ('g75920ee3', 'seller_id', None, LUKOIL, Q_IHC, RIA),
    ('g75920ee3', 'date', '2025-11-23', '2025-11-21', Q_NAT, NAT),
    ('g9fc75a9c', 'ind', 'Пищепром и напитки', 'Потребительские товары', Q_MX, VED_MX),
    ('g84fd8194', 'sum', '$20–22 млрд (по оценке)', 'Не раскрыта', Q_CH_VAL, URA),
    ('g84fd8194', 'eco.sum', '$20–22 млрд (по оценке)', 'Не раскрыта', Q_CH_VAL, URA),
    ('g84fd8194', 'seller_id', None, LUKOIL, Q_CH_SELL, HP),
    ('g61182014', 'seller', 'Николай Мельничук, Андрей Зайцев-Зотов, Марина Чадеева и Дмитрий Степанов',
     'Николай Мельничук, Андрей Зайцев-Зотов и Дмитрий Степанов', Q_YA_REG, REG % 'gc2c803f9'),
    ('g61182014', 'eco.finadv', 'Novus Capital — финансовый консультант продавцов', 'Публично не сообщалось', Q_YA_CONS, KOM_YA),
    ('g335d3cdc', 'date', '2025-11-10', '2025-11-11', Q_MK_REG, REG % 'g7e235832'),
    ('g3fb43064', 'sum', '6–7 млрд ₽ (по оценке)', '≈6 млрд ₽ (по оценке)', Q_IS_SUM, ABIREG),
    ('g3fb43064', 'eco.sum', '6–7 млрд ₽ (по оценке)', '≈6 млрд ₽ (по оценке)', Q_IS_SUM, ABIREG),
    ('g3fb43064', 'date', '2025-11-05', '2025-11-07', Q_IS_REG, DN % '1093652000474'),
    ('g3fb43064', 'eco.share', 'Завод «Исток» вместе с транспортной компанией ООО «Исток-Логистик».',
     '100% долей ООО «Исток» и ООО «Исток-Логистик»', Q_IS_REG + ' … ' + Q_IS_AKM, DN % '1093652000474'),
    ('ge56325d9', 'date', '2025-11-01', '2025', Q_GP, DP),
    ('ga218f75c', 'sum', '≈500 млн ₽ (по оценке)', 'Не раскрыта', Q_KO_PESH, KOM_KO),
    ('ga218f75c', 'eco.sum', '≈500 млн ₽ (по оценке)', 'Не раскрыта', Q_KO_PESH, KOM_KO),
    ('gbb7e25e1', 'sum', '≈$200 млн (по данным Известий; альт. оценки 15–16 млрд ₽ или EV ≈50 млрд ₽)',
     '15–16 млрд ₽ (по оценке)', Q_FS, KOM_FS),
    ('gbb7e25e1', 'eco.sum', '≈$200 млн (по данным Известий; альт. оценки 15–16 млрд ₽ или EV ≈50 млрд ₽)',
     '15–16 млрд ₽ (по оценке)', Q_FS, KOM_FS),
    ('gbb7e25e1', 'ind', 'Транспорт и логистика', 'Гостиницы и туризм', Q_FS_IND, KOM_FS),
]
# смена формы и отметки без нового факта
SET = [
    ('g61182014', 'date_basis', None, 'registry'),
    ('g335d3cdc', 'date_basis', None, 'registry'),
    ('g3fb43064', 'date_basis', None, 'registry'),
    ('g8af20254', 'date_basis', None, 'registry'),
    ('ga218f75c', 'date_basis', None, 'registry'),
    ('gd66af0f7', 'date_basis', None, 'registry'),
    ('g9fc75a9c', 'date_basis', None, 'registry'),
]
RETRACT = [
    ('g84fd8194', 'sum', '$20–22 млрд (по оценке)'),
    ('g61182014', 'eco.finadv', 'Novus Capital — финансовый консультант продавцов'),
    ('g3fb43064', 'sum', '6–7 млрд ₽ (по оценке)'),
    ('ga218f75c', 'sum', '≈500 млн ₽ (по оценке)'),
    ('g61182014', 'seller', 'Николай Мельничук, Андрей Зайцев-Зотов, Марина Чадеева и Дмитрий Степанов'),
]
NOTES = [
    ('g61182014', 'no_profile.seller',
     'продавцы — физлица по ЕГРЮЛ ООО «Ясно.Лайв» (Мельничук 61,9%, Зайцев-Зотов 18%, Степанов 3,1%, вышли 14.11.2025); '
     'профили людям не заводятся (вычитка 12.11.2026, m012)'),
    ('g335d3cdc', 'no_profile.seller',
     'продавец — физлицо Андрей Бредихин (ЕГРЮЛ ООО «Кама-Трейд Татарстан», вышел 11.11.2025); профиль человеку не заводится '
     '(вычитка 12.11.2026, m012)'),
    ('ga218f75c', 'no_profile.seller',
     'продавец — физлицо Светлана Сулейманова (ЕГРЮЛ ООО «ПТК «Колос»»: 100% → 5% 01.11.2025, вышла 17.12.2025) '
     '(вычитка 12.11.2026, m012)'),
    ('gd66af0f7', 'no_profile.seller',
     'продавец — физлицо Илья Рагозин (ЕГРЮЛ ООО «Молоко Групп»: 99% → 74,249% 17.10.2025) (вычитка 12.11.2026, m012)'),
    ('g3fb43064', 'no_profile.seller',
     'продавец — физлицо Руслан Вдовин (ЕГРЮЛ ООО «Исток», ОГРН 1093652000474: вышел 07.11.2025) (вычитка 12.11.2026, m012)'),
]
COMPANY = [
    ('g0324fa7b', 'desc',
     'Специализированное финансовое общество через структуру «Аргентум» фонда «Стелла» (учредитель Ольга Исаева); в 2025 году '
     'купило 100% онлайн-платформы психологической помощи «Ясно».',
     'Акционерное общество, которое через специализированное финансовое общество «Аргентум» принадлежит фонду «Стелла» '
     '(учредитель — Ольга Исаева); в 2025 году купило 100% сервиса психологической помощи «Ясно».'),
    ('gaa6cbfd3', 'desc',
     'Производитель косметики Mixit; в 2025 году фонды Pre-IPO 1 и Pre-IPO 2 «ВИМ Инвестиции» продали свои 32,98% доли самой '
     'компании (казначейский выкуп), заработав 1,9x за 1,5 года — от IPO на Мосбирже Mixit отказался.',
     'Управляющая компания производителя косметики Mixit; в ноябре 2025 года фонды Pre-IPO 1 и Pre-IPO 2 «ВИМ Инвестиций» '
     'продали свои 32,98% самой компании, а от IPO Mixit отказался.'),
    ('gaa6cbfd3', 'ind', 'Пищепром и напитки', 'Потребительские товары'),
    ('g2e85f5e5', 'ind', 'Транспорт и логистика', 'Гостиницы и туризм'),
    ('gf8d55310', 'desc', 'Кондитерская фабрика в Челябинске; в 2023 году 95% долей выкупил предприниматель Акульчев.',
     'Кондитерская фабрика в Челябинске (ООО «ПТК «Колос»»), основана в 2007 году; в ноябре 2025 года 95%, а в декабре — '
     'остальные 5% купила компания «Акульчев».'),
    ('gf0296008', 'desc', 'Предприниматель; в 2023 году купил 95% долей кондитерской фабрики «Колос» в Челябинске.',
     'Производитель мягких вафель, печенья и мороженого (ООО «ПК «Акульчев»»), основан в 1995 году Сергеем Акульчевым; в 2025 '
     'году купил челябинскую кондитерскую фабрику «Колос».'),
    ('g388b0f09', 'desc',
     'Бизнесмен, владелец ГК «Интегра»; в 2023–2026 годах купил у Росимущества «Первую образцовую типографию» и газодобытчика '
     '«Южгазэнерджи», а также маслозавод «Исток» в Лисках.',
     'Бизнесмен, бывший вице-президент нефтесервисной ГК «Интегра»; в 2023–2026 годах купил у государства «Первую образцовую '
     'типографию» и газодобытчика «Южгазэнерджи», а также маслозавод «Исток» в Лисках.'),
    ('gce487d25', 'desc',
     'Лискинский маслоэкстракционный завод в Воронежской области, производит нерафинированное растительное масло и подсолнечный шрот.',
     'Маслоэкстракционный завод в Лисках Воронежской области (ООО «Исток», зарегистрировано в 2009 году); в ноябре 2025 года '
     'Руслан Вдовин продал его Денису Избрехту.'),
    ('g3a6a6971', 'desc',
     'Торгово-развлекательный центр; в 2025 году группа «Аврора» купила 50% у китайской SIIC, доведя владение до 100% — вторую '
     'половину годом ранее выкупила у финской SRV Central Properties.',
     'Торгово-развлекательный центр в Петербурге, построен в 2013 году; в 2025 году половину компании-владельца у китайской SIIC '
     'купила группа «Аврора», вторая половина с 2024 года у Central Properties.'),
]
# Реестр ФНС: профиль ООО «Исток» стоял на ИНН чужого юрлица.
REG_EDIT = [
    ('gce487d25', '3652001387', {
        'decision': 'confirmed', 'inn': '3652011018',
        'reason': ('Вычитка m012 (2026-11-12): ООО «Исток», Лиски, ОГРН 1093652000474, ИНН 3652011018 — декларация пожарной '
                   'безопасности МЧС (масло-экстракционная площадка ООО «Исток») и история участников datanewton по ОГРН: '
                   'Вдовин 100% → Избрехт 100% 07.11.2025, как в Ъ и AK&M. Прежний ИНН 3652001387 — АО МЭЗ «Лискинский», '
                   'другое юрлицо.'),
        'date': '2026-11-12'}),
]


def _get(obj, field):
    for p in field.split('.'):
        obj = obj.get(p) if isinstance(obj, dict) else None
    return obj


def _set(obj, field, value):
    parts = field.split('.')
    for p in parts[:-1]:
        obj = obj.setdefault(p, {})
    obj[parts[-1]] = value


def _apply(data):
    import fact_edit_guard
    import review
    deals = {d['id']: d for d in data['deals']}
    for cid, field, old, new, quote, url in ONE_OFF:
        card = deals[cid]
        if _get(card, field) == new:
            continue
        assert _get(card, field) == old, (cid, field, _get(card, field))
        _set(card, field, new)
        fact_edit_guard.log(card, field, new, quote, url, BY)
        # записи таблицы правок на это поле — применены раньше и переписаны здесь
        marks = card.setdefault('proofread_absorbed', {}).setdefault(field, [])
        for f in review.FIXES:
            if f['id'] == cid and f['field'] == field and f['new'] is not None and f['new'] != new:
                fp = review.fix_fingerprint(f['new'])
                if fp not in marks:
                    marks.append(fp)
        if not marks:
            card['proofread_absorbed'].pop(field)
    for cid, field, old, new in SET:
        if _get(deals[cid], field) == new:
            continue
        assert _get(deals[cid], field) == old, (cid, field, _get(deals[cid], field))
        _set(deals[cid], field, new)
    for cid, field, value in RETRACT:
        lst = deals[cid].setdefault('retracted', {}).setdefault(field, [])
        if value not in lst:
            lst.append(value)
    for cid, path, value in NOTES:
        notes = deals[cid].setdefault('accepted_notes', {})
        if _get(notes, path) is not None:      # заметка о стороне уже есть — не переписываем
            continue
        _set(notes, path, value)
    for comp, field, old, new in COMPANY:
        c = data['companies'][comp]
        if c.get(field) == new:
            continue
        assert c.get(field) == old, (comp, field, c.get(field))
        c[field] = new


def _registry(write):
    import fns_registry
    rows = json.load(open(REG_JSON, encoding='utf-8'))
    changed = False
    for cid, old_inn, row in REG_EDIT:
        hits = [i for i, r in enumerate(rows) if r.get('company_id') == cid]
        assert len(hits) == 1, (cid, hits)
        r = rows[hits[0]]
        if r.get('inn') == row['inn']:
            continue
        assert r.get('inn') == old_inn, (cid, r)
        assert fns_registry.inn_is_valid(row['inn'])
        assert row['inn'] not in {x.get('inn') for x in fns_registry.REGISTRY if x.get('company_id') != cid}
        rows[hits[0]] = dict({'company_id': cid}, **row)
        changed = True
    if write and changed:
        with open(REG_JSON, 'w', encoding='utf-8') as fh:
            json.dump(rows, fh, ensure_ascii=False, indent=1)
    return changed


# Старые нарушения правил текста, которые эта партия исправила: убрать из списка известных
# (test_card_text_follows_the_house_rules требует, чтобы исправленное ушло из базовой линии).
BASELINE_GONE = ['gbb7e25e1|eco.sum|source_note|2b7b82303c']


def _baseline(write):
    path = os.path.join(ROOT, 'pipeline', 'text_rules_baseline.json')
    raw = open(path, encoding='utf-8').read()
    b = json.loads(raw)
    left = [k for k in b['known'] if k not in BASELINE_GONE]
    if len(left) == len(b['known']) or not write:
        return
    b['known'] = left
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(b, fh, ensure_ascii=False, indent=1)
        if raw.endswith('\n'):
            fh.write('\n')


if __name__ == '__main__':
    import mass_edit_guard
    write = '--write' in sys.argv
    data = json.load(open(DATA, encoding='utf-8'))
    before = copy.deepcopy(data)
    _apply(data)
    mass_edit_guard.check(before, data, os.environ.get('MASS_OK'))
    reg = _registry(False)
    print('Разовая часть m012: фактов %d, снятых значений %d, заметок %d, профилей %d, строк реестра ФНС %d — проверки '
          'пройдены.' % (len(ONE_OFF), len(RETRACT), len(NOTES), len(COMPANY), len(REG_EDIT) if reg else 0))
    if write:
        fresh = json.load(open(DATA, encoding='utf-8'))      # перечитать прямо перед записью
        before = copy.deepcopy(fresh)
        _apply(fresh)
        mass_edit_guard.check(before, fresh, os.environ.get('MASS_OK'))
        with open(DATA, 'w', encoding='utf-8') as fh:
            json.dump(fresh, fh, ensure_ascii=False, indent=1)
        _registry(True)
        _baseline(True)
        print('Записано.')
    else:
        print('Сухой прогон. Запись — с ключом --write.')
