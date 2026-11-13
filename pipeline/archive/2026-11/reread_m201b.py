# -*- coding: utf-8 -*-
"""Вычитка базы, марафон 12 ноября 2026, партия m201, часть вторая: g5da91c40, g4ba9150f, gadb5b474, g92c06203,
g942865d3, g38e5718e, g577a83e0 (и снятый повтор extra у g43b0394d из первой части).

g5da91c40 (EMC / «Семейный доктор») — Ъ 8178089 (31.10.2025, 21:55) и 8231432, Интерфакс 1055991, Ведомости
            (31.10.2025 и 08.06.2026). Сделка объявлена завершенной 31 октября 2025 года — дата 1 октября не была днем
            события. Оценка «кредит косвенно подтверждает оценку» — нашего сочинения, снята; финансы и контекст — по статьям.
g4ba9150f (Светогорский ЦБК / «ЭвоКом») — Ъ 8141163, 8141143, 8210001, Retail.ru (30.03.2026), реестр ООО «ЭвоКом» по
            ОГРН 1024700877200 (с 19.05.2025 единственный участник — АО «Эдельвейс», после этого записей нет). Договор
            подписан в середине октября 2025 года, день закрытия не назван — дата годом. Продавец: акционеры АО
            «Эдельвейс» в реестре не видны (на конец 2024 года — Гущин-Кузнецов, «ЭсСиЭй Хайджин Продактс», ЗПИФ
            «ААА-Иридиум», ЗПИФ «Аммонит»; позже — Максим Лебедев), кто продал пакет — не раскрыто: пусто, где
            искали — в accepted_notes. Отрасль по предмету (бумажная гигиена) — «Потребительские товары».
gadb5b474 (ИГ Геоинвест / «Техсервис») — Ъ 8100314, zolteh.ru, реестр (01.10.2025 вошел ИГ Геоинвест). Продавцы —
            ООО «РТ-Развитие бизнеса» (35%) и ООО «Гурбей Золото» (65%), а не «Ростех» в целом; ссылка на профиль
            госкорпорации снята (профиля под юрлицо продавца нет).
g92c06203 (Befortune Trading / Forward) — Ъ 8497943, реестр ООО «Спэйс» (29.09.2025: 67% Флигеля перешли к
            Befortune Trading (HK) Limited, Лян Цзяньсюн — 33% лично). Покупатель в схеме — гонконгская компания из
            реестра, Лян — ее единственный акционер (в прозе). Отрасль велосипедов — не «Автопром».
g942865d3 (УК «Первая» / «Интерскол») — Ведомости, interskol.ru (23.09.2025 — объявление «инвестирует»), НКР
            (19.06.2026: новые инвесторы вошли в акционеры), smart-lab (pre-IPO 2024). День закрытия не назван — дата
            годом. «Это независимо подтверждает, что цель достигнута» — наш вывод, снят.
g38e5718e (Ордовский-Танаевский Бланко / «Ной-М») — Ъ 8062381, Lenta.ru (пересказ Ъ), реестр (17.09.2025).
g577a83e0 («Ригла» / «Аптека25.рф») — Vademecum, Ведомости, Фармвестник; по ЕГРЮЛ и СПАРК «Ригла» стала владельцем
            трех обществ 12 сентября 2025 года (а не 15-го — день статьи).

Запуск: без ключа — сухой прогон; --write — запись (база перечитывается прямо перед записью, assert на старые
значения, повторный запуск ничего не ломает). Правка факта — с fact_edit_guard.log.
"""
import copy
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BY = 'вычитка 12 ноября 2026, партия m201'
KOM_SD = 'https://www.kommersant.ru/doc/8178089'
KOM_ZEWA = 'https://www.kommersant.ru/doc/8141163'
DN_EVOKOM = 'https://datanewton.ru/api/v2/history?ogrn=1024700877200&startDate=2000-01-01&attributes=OWNERS'
KOM_TS = 'https://www.kommersant.ru/doc/8100314'
REG_TS = 'https://projectcompass.ru/api/companies/gd28693f6/fns'
KOM_FW = 'https://www.kommersant.ru/doc/8497943'
REG_FW = 'https://projectcompass.ru/api/companies/gbb804a70/fns'
VED_IS = 'https://www.vedomosti.ru/investments/articles/2025/09/23/1141149-uk-pervaya-investiruet-v-interskol'
SL_IS = 'https://smart-lab.ru/blog/news/1089394.php'
KOM_PZ = 'https://www.kommersant.ru/doc/8062381'
REG_PZ = 'https://projectcompass.ru/api/companies/g37927fa2/fns'
VA_RG = 'https://vademec.ru/news/2025/09/15/rigla-priobrela-vse-tochki-seti-apteka25-rf-iz-vladivostoka/'
VED_RG = 'https://www.vedomosti.ru/business/articles/2025/09/15/1139447-rigla-kupila-set-aptek'

SET = [
    ('g43b0394d', 'extra', '—', '', ''),
    ('g5da91c40', 'date', '2025-10-31',
     'Европейский медицинский центр выкупил 75% в сети клиник «Семейный доктор» 31.10.2025, 21:55 Европейский '
     'медицинский центр (ЕМЦ) приобрел 75% акций в сети клиник «Семейный доктор».', KOM_SD),
    ('g5da91c40', 'date_basis', 'closing', '', ''),
    ('g5da91c40', 'title', 'Европейский медицинский центр купил 75% «Семейного доктора»',
     'Европейский медицинский центр (ЕМЦ) приобрел 75% акций в сети клиник «Семейный доктор».', KOM_SD),
    ('g4ba9150f', 'date', '2025',
     'По их словам, договор купли-продажи был подписан в конце прошлой недели, сделка должна быть закрыта в '
     'ближайшие дни.', KOM_ZEWA),
    ('g4ba9150f', 'title', 'Светогорский ЦБК купил «ЭвоКом»',
     'Крупный производитель бумажных санитарно-гигиенических изделий (СГИ) «Эволюция комфорта» («ЭвоКом») перейдет '
     'под контроль Светогорского ЦБК (бренд SvetoCopy)', KOM_ZEWA),
    ('g4ba9150f', 'ind', 'Потребительские товары', '', ''),
    ('g4ba9150f', 'law.terms', '—', '', ''),
    ('g4ba9150f', 'extra', '—', '', ''),
    ('gadb5b474', 'seller', 'ООО «РТ-Развитие бизнеса» и ООО «Гурбей Золото»',
     'До сделки «РТ-Развитие бизнеса» владела 35% «Техсервиса», 65% было у ООО «Гурбей Золото» Игоря Елисеева и '
     'экс-гендиректора девелоперской группы «Самолет» Антона Елистратова.', KOM_TS),
    ('gadb5b474', 'seller_id', None, '', ''),
    ('gadb5b474', 'title', 'АО «ИГ Геоинвест» купило ООО «Техсервис»',
     'В октябре 100% «Техсервиса» получило АО «ИГ Геоинвест»', KOM_TS),
    ('gadb5b474', 'date_basis', 'registry', '', ''),
    ('gadb5b474', 'extra', '—', '', ''),
    ('g92c06203', 'buyer', None,
     '2025-09-29: Флигель Максим Яковлевич (67%) вышел из участников; вошли «Бефорчун Трейдинг (ХК) Лимитед» — 67% '
     'и Лян Цзяньсюн — 33%.', REG_FW),
    ('g92c06203', 'buyer_name', 'Befortune Trading (HK) Limited',
     'Гонконгская Befortune Trading стала основным владельцем пермского ООО «Спэйс», которому принадлежит бренд '
     'велосипедов Forward', KOM_FW),
    ('g92c06203', 'seller', 'Максим Флигель',
     'Компания получила 67% долей, которые ранее контролировал Максим Флигель.', KOM_FW),
    ('g92c06203', 'title', 'Befortune Trading купил 67% Forward',
     'Гонконгская Befortune Trading стала основным владельцем пермского ООО «Спэйс», которому принадлежит бренд '
     'велосипедов Forward', KOM_FW),
    ('g92c06203', 'ind', 'Потребительские товары', '', ''),
    ('g92c06203', 'date_basis', 'registry', '', ''),
    ('g942865d3', 'title', 'УК «Первая» купила долю в «Интерсколе»',
     'Управляющая компания (УК) «Первая» инвестирует 1 млрд руб. в разработчика, производителя и продавца '
     'электроинструментов «Интерскол», узнали «Ведомости».', VED_IS),
    ('g942865d3', 'date', '2025',
     'Управляющая компания (УК) «Первая» инвестирует 1 млрд руб. в разработчика, производителя и продавца '
     'электроинструментов «Интерскол», узнали «Ведомости».', VED_IS),
    ('g38e5718e', 'title', 'Ростислав Ордовский-Танаевский Бланко купил 60% сети «ПиццаН»',
     'Ростислав Ордовский-Танаевский Бланко 17 сентября получил 60% в ООО «Ной-М», следует из данных ЕГРЮЛ. Эта '
     'компания управляет пиццериями «ПиццаН».', KOM_PZ),
    ('g38e5718e', 'date_basis', 'registry', '', ''),
    ('g38e5718e', 'extra', '—', '', ''),
    ('g577a83e0', 'date', '2025-09-12',
     'Федеральная аптечная сеть «Ригла» 12 сентября 2025 года стала владельцем трех новых дочерних компаний, '
     'зарегистрированных во Владивостоке, как указано в СПАРК-Интерфакс.', VA_RG),
    ('g577a83e0', 'date_basis', 'registry', '', ''),
    ('g577a83e0', 'title', '«Ригла» купила «Аптеку25.рф»',
     '«Ригла» (входит в группу « Протек » Вадима Якунина), как следует из ее сообщения, приобрела сеть «Аптека25.рф»',
     VED_RG),
]

OLD = {
    'g43b0394d|extra': 'ООО «РВБ» (Группа WBR) — совместная компания Wildberries и Russ Outdoors с долями 65% и 35% — '
                       'купило 100% долей рекламного агентства ООО «Инфо-Ю». Продавцы — Татьяна Плахотникова (80%) и '
                       'Леонид Рудой (20%).',
    'g5da91c40|date': '2025-10-01',
    'g5da91c40|date_basis': None,
    'g5da91c40|title': 'Европейский медицинский центр приобрел 75% сети клиник «Семейный доктор»',
    'g4ba9150f|date': '2025-10-01',
    'g4ba9150f|title': 'Светогорский ЦБК приобрел ООО «ЭвоКом» (производителя Zewa и Libresse)',
    'g4ba9150f|ind': 'Химия и удобрения',
    'g4ba9150f|law.terms': 'В июле 2023 года российские активы продала Essity — шведская компания, которой принадлежат '
                           'бренды Zewa, Libresse, Tork и Tena. Дальше выпуском продукции в стране занималась «Эссити», а '
                           'в июне 2024 года эта компания сменила название на «Эволюция комфорта».',
    'g4ba9150f|extra': 'Светогорский ЦБК получил пакет в «ЭвоКом». Точная дата закрытия публично не называлась, о '
                       'завершении сделки стало известно позже. Покупатель получил доступ к сырью (целлюлозе) и '
                       'преимущества в утилизации отходов через механизм РОП.',
    'gadb5b474|seller': 'Ростех',
    'gadb5b474|seller_id': 'g7802e51e',
    'gadb5b474|title': 'Ростех продал золотодобывающий актив ООО «Техсервис» компании АО «ИГ Геоинвест»',
    'gadb5b474|date_basis': None,
    'gadb5b474|extra': 'Закрытая сделка по продаже имущественных прав на ООО «Техсервис» (владелец золотодобывающих '
                       'участков «Гурбей» и «Светино» в Иркутской области). Продавцами выступили АО «РТ-Развитие '
                       'бизнеса» (35%, входит в Ростех) и ООО «Гурбей Золото» (65%, совладельцы Игорь Елисеев и Антон '
                       'Елистратов). Покупателем стала АО «ИГ Геоинвест».',
    'g92c06203|buyer': 'gfb0dc8c7',
    'g92c06203|buyer_name': None,
    'g92c06203|seller': 'Флигель Максим Яковлевич',
    'g92c06203|title': 'Китайский бизнесмен Лян Цзяньсюн выкупил контрольный пакет велосипедного производителя Forward',
    'g92c06203|ind': 'Автопром',
    'g92c06203|date_basis': None,
    'g942865d3|title': 'УК «Первая» инвестировала 1 млрд рублей в «Интерскол»',
    'g942865d3|date': '2025-09-23',
    'g38e5718e|title': 'Ростислав Ордовский-Танаевский Бланко приобрел 60% долей в ООО «Ной-М» (сеть «ПиццаН»)',
    'g38e5718e|date_basis': None,
    'g38e5718e|extra': 'Ростислав Ордовский-Танаевский Бланко, владелец «Росинтер Ресторантс Холдинг» и холдинга «Ростик», '
                       'получил 60% долей ООО «Ной-М» в обмен на консультирование. Продавец Владимир Мехришвили снизил '
                       'свою долю до 20%, еще по 10% остались у Алексея Чайки и Светланы Берсневой.',
    'g577a83e0|date': '2025-09-15',
    'g577a83e0|date_basis': None,
    'g577a83e0|title': '«Ригла» приобрела аптечную сеть «Аптека25.рф» в Приморском крае',
}

SRC_ADD = [
    ('g4ba9150f', 'ЕГРЮЛ', DN_EVOKOM),
    ('gadb5b474', 'ЕГРЮЛ', REG_TS),
    ('g92c06203', 'ЕГРЮЛ', REG_FW),
    ('g942865d3', 'Smart-Lab', SL_IS),
    ('g38e5718e', 'ЕГРЮЛ', REG_PZ),
]

COMPANY = [
    ('g7e5ae30b', 'legal_short', 'АО «Семейный доктор»'),
    ('g4188b146', 'legal_short', 'АО «ИГ Геоинвест»'),
    ('gbb804a70', 'legal_short', 'ООО «Спэйс»'),
    ('gbb804a70', 'ind', 'Потребительские товары'),
    ('gbb804a70', 'desc', 'Владелец велосипедного бренда Forward; в сентябре 2025 года 67% долей у Максима Флигеля '
                          'получила гонконгская Befortune Trading, единственный акционер которой — китайский '
                          'предприниматель Лян Цзяньсюн (председатель Trinity Group); еще 33% принадлежат ему с 2014 года.'),
    ('g9decc157', 'name', 'Аптека25.рф'),
    ('g9decc157', 'legal_short', 'ООО «Аптека25.рф»'),
]
COMPANY_OLD = {
    'g7e5ae30b|legal_short': None,
    'g4188b146|legal_short': None,
    'gbb804a70|legal_short': None,
    'gbb804a70|ind': 'Автопром',
    'gbb804a70|desc': 'Владелец велосипедного бренда Forward; в сентябре 2025 года китайский бизнесмен Лян Цзяньсюн '
                      '(председатель Trinity Group) выкупил 67% долей у Максима Флигеля за более 1 млрд ₽ (по оценке), '
                      'доведя пакет, начиная с 33% с 2014 года, до 100%.',
    'g9decc157|name': 'аптечная сеть «Аптека25.рф»',
    'g9decc157|legal_short': None,
}

NOTES = {
    'g4ba9150f': {'no_profile': {'seller': 'Продавец не раскрыт. ООО «ЭвоКом» с 19.05.2025 целиком принадлежит АО '
                  '«Эдельвейс», и после этого участник в ЕГРЮЛ не менялся (datanewton по ОГРН 1024700877200); акционеров '
                  'АО реестр не показывает. Ъ 8141163: на конец 2024 года акционеры «Эдельвейса» — Николай '
                  'Гущин-Кузнецов, «ЭсСиЭй Хайджин Продактс», ЗПИФ «ААА-Иридиум» (по 20%), ЗПИФ «Аммонит» (35%), позже '
                  'по ЕГРЮЛ — Максим Лебедев. Искали: Ъ 8141163, 8141143, 8210001, Retail.ru, New-Retail, WebSearch по '
                  '«Эдельвейс» / «ЭвоКом» / Светогорский ЦБК — кто продал пакет, не названо.'}},
    'g92c06203': {'no_profile': {'buyer': 'Befortune Trading (HK) Limited — гонконгская компания, единственный акционер '
                  'Лян Цзяньсюн (Ъ 8497943 по реестру Гонконга); российского ИНН нет, профиль не заводится.'}},
}

REGISTRY = []


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


def _apply(data):
    sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
    sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
    import fact_edit_guard
    import review
    deals = {d['id']: d for d in data['deals']}
    comps = data['companies']
    changed = 0
    for cid, field, new, quote, url in SET:
        card = deals[cid]
        cur = _get(card, field)
        if cur == new:
            continue                                   # уже применено
        assert cur == OLD['%s|%s' % (cid, field)], (cid, field, cur)
        _set(card, field, new)
        changed += 1
        if field in fact_edit_guard.FACT_FIELDS:
            assert quote and url, (cid, field)
            fact_edit_guard.log(card, field, new, quote, url, BY)
        marks = card.setdefault('proofread_absorbed', {}).setdefault(field, [])
        for f in review.FIXES:
            if (f.get('id'), f.get('field')) == (cid, field) and f.get('new') != new:
                fp = review.fix_fingerprint(f['new'])
                if fp not in marks:
                    marks.append(fp)
        if not marks:
            card['proofread_absorbed'].pop(field, None)
    for cid, label, url in SRC_ADD:
        src = deals[cid].setdefault('src', [])
        if not any(u == url for _l, u in src):
            src.append([label, url])
    for cid, notes in NOTES.items():
        acc = deals[cid].setdefault('accepted_notes', {})
        for k, v in notes.items():
            if isinstance(v, dict):
                acc.setdefault(k, {}).update(v)
            else:
                acc[k] = v
    for comp, field, new in COMPANY:
        cur = comps[comp].get(field)
        if cur == new:
            continue
        assert cur == COMPANY_OLD['%s|%s' % (comp, field)], (comp, field, cur)
        comps[comp][field] = new
    return changed


def _apply_registry(write):
    path = os.path.join(ROOT, 'pipeline', 'fns_registry.json')
    rows = json.load(open(path, encoding='utf-8'))
    for comp, old, new, reason in REGISTRY:
        row = [r for r in rows if r.get('company_id') == comp]
        assert len(row) == 1 and row[0].get('inn') in (old, new), (comp, row)
        row[0].update({'inn': new, 'decision': 'confirmed', 'reason': reason, 'date': '2026-11-12'})
    if write:
        json.dump(rows, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        open(path, 'a', encoding='utf-8').write('\n')


if __name__ == '__main__':
    sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
    path = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
    base = json.load(open(path, encoding='utf-8'))
    new = copy.deepcopy(base)
    n = _apply(new)
    _apply_registry(False)
    import fact_edit_guard
    print('fact_edit_guard:', fact_edit_guard.problem(base, new) or 'чисто')
    print('Полей к записи: %d (из %d в списке).' % (n, len(SET)))
    if '--write' in sys.argv:
        import mass_edit_guard
        fresh = json.load(open(path, encoding='utf-8'))      # перечитать прямо перед записью
        before = copy.deepcopy(fresh)
        _apply(fresh)
        mass_edit_guard.check(before, fresh, key=os.environ.get('MASS_OK'))
        json.dump(fresh, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        _apply_registry(True)
        print('Записано.')
    else:
        print('Сухой прогон. Запись — с ключом --write.')
