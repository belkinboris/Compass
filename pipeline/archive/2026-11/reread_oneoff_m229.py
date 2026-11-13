# -*- coding: utf-8 -*-
"""Вычитка, марафон 12 ноября 2026, партия m229 (короткая проверка карточек об уходе
иностранных владельцев, 2022 год): правки, которые не ложатся в таблицу review.py
(снятие стороны, новые профили, ИНН в реестр, дата по реестру, элемент прозы).

* gfb282142 (Jotun / «Атомстройкомплекс»): предметом стоял профиль «Литум» — это
  ООО ГК «Литум» (ИНН 6685208470, создано в 2023 году), головная компания группы, а не
  купленный завод. Завод — ООО «Йотун Пэйнтс», ОГРН 1047855160550, ИНН 7805360880, с 26
  августа 2022 года ООО «Литум» (api-fns egr: НаимЮЛСокр «ЙОТУН ПЭЙНТС» 2004-12-08 ~
  2022-08-25; СПАРК-Интерфакс, поиск по ИНН 7805360880: ООО «Литум», Тосненский район,
  д. Аннолово, ОГРН 1047855160550, производство красок). По истории участников ЕГРЮЛ
  100% от Jotun A/S (до 2022-07-28) перешли 2022-07-29 к ООО «Атомстройкомплекс-
  Промышленность» (ИНН 6685028781, ОГРН 1136685004587; участники Валерий Ананьев и Павел
  Кузнецов по 50%; в СПАРК — управляющая компания), а не к АО «Корпорация
  «Атомстройкомплекс»». Покупатель и предмет — новыми профилями, ИНН — в реестр.
* gd0af0377 (Oerlikon), g50412a76 (Mediascope): покупатель «местный менеджмент» /
  «Менеджмент Mediascope» — нераскрытая сторона: поле пусто (docs/reread_checklist.md,
  «Стороны и предмет»); имена в источниках не названы, Mediascope прямо отказалась
  уточнить, кто подразумевается под менеджментом (New Retail со слов компании).
* g16540a36 (Boreo / YE Russia): «YE Russia» — АО «ЮЕ-Интернейшнл» (с 2023 года АО «ЮЕ
  Тех»), ИНН 7810943817, ОГРН 1027804902344: api-fns egr — генеральный директор с 2015
  по ноябрь 2022 года Пенни Юрье Мауно Олави (гражданин Финляндии), прежнее имя
  «ЮЕ-ИНТЕРНЕЙШНЛ» до 2023-08-06; tapki.com — АО «ЮЕ Тех», ИНН 7810943817, ОГРН
  1027804902344, оптовая торговля электронным оборудованием; Castrén & Snellman — Yrjö
  Pönni «current General Director and 10% shareholder of YE Russia». Предмет — профилем,
  доля — «90% акций АО «ЮЕ-Интернейшнл»». Способ оплаты (8000 акций Boreo) — не оценка:
  из eco.val в eco.fin.
* gee7be9ef (Luxoft): продавец текстом «Luxoft International (DXC Technology)» стоял в
  паре с профилем Luxoft Holding, которого в реестре участников нет. По api-fns egr
  (история участников ООО «Люксофт Профешнл», ИНН 7713605227) до 2022-04-19 — кипрская
  Luxoft International Company Limited (99%) и Luxoft UK Limited (1%).
* g070084ad (Wärtsilä): по ЕГРЮЛ 100% до 2022-07-11 у А/О «Вяртсиля Технолоджи»
  (Wärtsilä Technology Oy Ab), продавец — оно.
* g5192332c (Харьяга): в law.appr — пересказ прессы «(по данным Нефтегаз.RU)»; в
  eco.context TotalEnergies договорилась о продаже доли не «тогда же» (в мае), а в июле
  2022 года (Коммерсантъ, 06.07.2022).

    python3 pipeline/archive/2026-11/reread_oneoff_m229.py [--write]

Повторный запуск ничего не меняет («уже применено»).
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402
import fns_notes_to_registry  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
REG = os.path.join(ROOT, 'pipeline', 'fns_registry.json')
BY, DAY = 'reread_oneoff_m229', '2026-11-13'
EGR = 'api-fns.ru egr (история участников ЕГРЮЛ)'

LITUM = 'g_litum_tosno_7805360880'
ASKP = 'g_askprom_6685028781'
YE = 'g_ye_tech_7810943817'

Q_LITUM = ('ЕГРЮЛ ООО «Литум» (до 25.08.2022 ООО «Йотун Пэйнтс»), ИНН 7805360880, ОГРН 1047855160550: '
           'Jotun A/S — 100% до 2022-07-28; ООО «Атомстройкомплекс-Промышленность» (ИНН 6685028781) — 100% '
           'с 2022-07-29 по 2023-10-24; АО ПК «Литум» — с 2023-10-25.')
Q_CASTREN = ('We advised Boreo Plc in a transaction in which it sold its 90% shareholding in the electronic component '
             'distribution business in Russia (“YE Russia”) to companies controlled by Mr. Yrjö Pönni, current General '
             'Director and 10% shareholder of YE Russia.')
CASTREN = 'https://www.castren.fi/cases/cases-2022/boreo2/'
Q_YE = ('ЕГРЮЛ АО «ЮЕ Тех» (до 06.08.2023 АО «ЮЕ-Интернейшнл»), ИНН 7810943817: генеральный директор с 2015 по '
        '29.11.2022 — Пенни Юрье Мауно Олави, гражданин Финляндии. ' + Q_CASTREN)
Q_LUX = ('ЕГРЮЛ ООО «ИБС Инфинисофт» (до 03.05.2022 ООО «Люксофт Профешнл»), ИНН 7713605227: МКК «Люксофт '
         'Интернэшнл Кампани Лимитед» (Кипр) — 99% и Люксофт Юкей Лимитед — 1% до 2022-04-19; с 2022-04-20 — '
         'АО «ИБС ИТ Услуги» 99% и ООО «ИБС» 1%.')
Q_WAR = ('ЕГРЮЛ ООО «В-Восток» (ИНН 7841339690): 2022-07-11 вышло А/О Вяртсиля Технолоджи (100%), вошел Норцев '
         'Константин Геннадьевич (100%).')
Q_OERL = ('Oerlikon has entered into an agreement with the local management team to sell all its operations in '
          'Russia. — имена покупателей не названы.')
OERL = 'https://oerlikon.com/en/company/media/press-releases/exited-russian-operations'
Q_MSC = ('«В сентябре 2022 года была достигнута финальная договоренность, в рамках которой Kantar передал свои '
         'российские активы менеджменту Mediascope», – сообщили РБК в Mediascope, отказавшись назвать условия сделки '
         'и точные сроки. А также в пресс-службе не уточнили, кто именно подразумевается под «менеджментом».')
MSC = 'https://new-retail.ru/novosti/retail/kantar_prodal_rossiyskie_aktivy_mestnomu_menedzhmentu6937/'
Q_KOM = ('«Зарубежнефть» приобретет у французской TotalEnergies, которая выходит из российской нефтяной отрасли, ее '
         'долю в 20% в Харьягинском месторождении. В мае об аналогичной договоренности по своим 30% в Харьяге '
         'объявляла норвежская Equinor. (06.07.2022)')
KOM = 'https://kommersant.ru/doc/5448063'

# (карточка, поле, было, стало, цитата, адрес); стало None — поле снимается
DEAL_EDITS = [
    ('gfb282142', 'target', 'g4b22714c', LITUM, Q_LITUM, EGR),
    ('gfb282142', 'buyer', 'g141b412e', ASKP, Q_LITUM, EGR),
    ('gfb282142', 'seller', 'Jotun', 'Jotun A/S', Q_LITUM, EGR),
    ('gfb282142', 'date_basis', None, 'registry', Q_LITUM, EGR),
    ('gd0af0377', 'buyer_name', 'местный менеджмент', None, Q_OERL, OERL),
    ('g50412a76', 'buyer_name', 'Менеджмент Mediascope', None, Q_MSC, MSC),
    ('g50412a76', 'title', 'Менеджмент Mediascope купил долю Kantar в измерителе',
     'Менеджмент Mediascope купил у Kantar 20% измерителя',
     'Доля британской компании в измерителе составляла 20%. В сентябре Kantar передал свои российские активы '
     'менеджменту Mediascope.', 'https://adindex.ru/news/media/2022/10/5/306940.phtml'),
    ('g16540a36', 'target', None, YE, Q_YE, EGR),
    ('g16540a36', 'asset', '90% в YE Russia', 'АО «ЮЕ-Интернейшнл» (YE Russia)', Q_YE, EGR),
    ('g16540a36', 'eco.share', '90% доли в YE Russia', '90% акций АО «ЮЕ-Интернейшнл»', Q_YE, EGR),
    ('g16540a36', 'title', 'Директор YE Russia Юрье Пенни купил у финской Boreo 90% компании',
     'Юрье Пенни купил 90% YE Russia у Boreo', Q_CASTREN, CASTREN),
    ('g16540a36', 'eco.val', 'Часть цены покупатель заплатил 8000 акций Boreo, которыми владел.', '—',
     'Osa kauppahinnasta suoritettiin ostajan omistamilla 8000 Boreon osakkeilla, mutta järjestelyn '
     'kokonaiskauppahintaa ei julkistettu.',
     'https://www.inderes.fi/content/analyst-comments/boreo-myy-venajan-liiketoimintonsa'),
    ('g16540a36', 'eco.fin', '—', 'Часть цены покупатель заплатил 8000 акций Boreo, которыми владел.',
     'Osa kauppahinnasta suoritettiin ostajan omistamilla 8000 Boreon osakkeilla, mutta järjestelyn '
     'kokonaiskauppahintaa ei julkistettu.',
     'https://www.inderes.fi/content/analyst-comments/boreo-myy-venajan-liiketoimintonsa'),
    ('gcdf0303d', 'title', 'Руководители российской Elopak купили компанию у норвежского владельца',
     'Местные руководители купили российский бизнес Elopak',
     'Norway\'s Elopak, a global supplier of carton packaging and filling equipment, said on Friday it had agreed '
     'to sell its Russian unit JSC Elopak to its local management.',
     'https://uk.finance.yahoo.com/news/norways-elopak-sells-russian-operations-073919511.html'),
    ('gee7be9ef', 'seller', 'Luxoft International (DXC Technology)',
     'Luxoft International Company Limited и Luxoft UK Limited', Q_LUX, EGR),
    ('gee7be9ef', 'seller_id', 'gc216a92e', None, Q_LUX, EGR),
    ('gee7be9ef', 'date_basis', None, 'registry', Q_LUX, EGR),
    ('g070084ad', 'seller', 'Wärtsilä', 'Wärtsilä Technology Oy Ab', Q_WAR, EGR),
    ('g070084ad', 'date_basis', None, 'registry', Q_WAR, EGR),
    ('g5192332c', 'law.appr',
     'Распоряжение правительства РФ от 25 июля 2022 года № 2034-р о передаче долей TotalEnergies и Equinor (по данным Нефтегаз.RU).',
     'Распоряжение правительства РФ от 25 июля 2022 года № 2034-р о передаче долей TotalEnergies и Equinor.',
     'Распоряжением от 25 июля 2022 г. № 2034-р правительство РФ обеспечило правовую базу перадачи активов.',
     'https://neftegaz.ru/tech-library/mestorozhdeniya/141704-kharyaginskoe-neftyanoe-mestorozhdenie/'),
]

# (карточка, поле, кусок было, кусок стало, цитата, адрес) — замена внутри прозы
TEXT_EDITS = [
    ('g5192332c', 'eco.context', 'Соглашение о выходе Equinor подписала в мае 2022 года, тогда же о продаже своей '
     'доли договорилась TotalEnergies.', 'Соглашение о выходе Equinor подписала в мае 2022 года, в июле о продаже '
     'своей доли договорилась TotalEnergies.', Q_KOM, KOM),
]

# (карточка, роль, было, стало) в accepted_notes.no_profile; стало None — заметка снимается
NOTES = [
    ('g16540a36', 'target', 'Русское юрлицо YE Russia источники не называют.', None),
    ('gee7be9ef', 'seller', None,
     'Продавцы по истории участников ЕГРЮЛ (api-fns): кипрская Luxoft International Company Limited (99%) и '
     'британская Luxoft UK Limited (1%) из группы DXC Technology; профилей нет. Профиль Luxoft Holding — их '
     'материнская компания, участником общества не был.'),
    ('g50412a76', 'buyer', 'Покупатель — менеджмент Mediascope без поименного списка; профиля нет.',
     'Покупатель — менеджмент Mediascope; кого именно компания имеет в виду, она не уточнила (New Retail, '
     'AdIndex, Ведомости). Mediascope — АО, акционеров ЕГРЮЛ не показывает.'),
]

NEW_COMPANIES = {
    LITUM: {'name': 'ООО «Литум» (Тосно)', 'ind': 'Химия и удобрения', 'legal_short': 'ООО «Литум»',
            'desc': 'Лакокрасочный завод в Тосненском районе Ленинградской области; до августа 2022 года — '
                    'ООО «Йотун Пэйнтс», российский завод норвежской Jotun.',
            'kpi': ['Профиль', 'Автоматический']},
    ASKP: {'name': 'ООО «Атомстройкомплекс-Промышленность»', 'ind': 'Холдинги',
           'legal_short': 'ООО «Атомстройкомплекс-Промышленность»',
           'desc': 'Екатеринбургская управляющая компания заводов группы «Атомстройкомплекс»; владельцы — '
                   'Валерий Ананьев и Павел Кузнецов, по 50%.',
           'kpi': ['Профиль', 'Автоматический']},
    YE: {'name': 'АО «ЮЕ Тех»', 'ind': 'Машиностроение', 'legal_short': 'АО «ЮЕ Тех»',
         'desc': 'Петербургский дистрибьютор электронных компонентов; до 2023 года — АО «ЮЕ-Интернейшнл», '
                 'российский бизнес YE финской Boreo.',
         'kpi': ['Профиль', 'Автоматический']},
}

REGISTRY = [
    {'company_id': LITUM, 'decision': 'confirmed', 'inn': '7805360880',
     'reason': 'Предмет карточки gfb282142 (завод Jotun). ООО «Литум», до 25.08.2022 ООО «Йотун Пэйнтс», ИНН '
               '7805360880, ОГРН 1047855160550, Ленинградская обл., Тосненский р-н, д. Аннолово. Совпало: (1) api-fns '
               'egr — те же ИНН и ОГРН, прежнее имя «Йотун Пэйнтс» (2004-12-08 ~ 2022-08-25), участники: Jotun A/S 100% '
               'до 2022-07-28, ООО «Атомстройкомплекс-Промышленность» с 2022-07-29, АО ПК «Литум» с 2023-10-25; '
               '(2) СПАРК-Интерфакс, поиск по ИНН: ООО «Литум», тот же адрес и ОГРН, производство красок и лаков. '
               'Профиль «Литум» (g4b22714c, ООО ГК «Литум», ИНН 6685208470) — головная компания группы, '
               'не этот завод (вычитка m229).',
     'date': DAY},
    {'company_id': ASKP, 'decision': 'confirmed', 'inn': '6685028781',
     'reason': 'Покупатель карточки gfb282142. ООО «Атомстройкомплекс-Промышленность», ИНН 6685028781, ОГРН '
               '1136685004587, Екатеринбург, ул. Белинского, 39. Совпало: (1) api-fns egr — те же ИНН и ОГРН, '
               'участники Ананьев В. М. и Кузнецов П. А. по 50%; в истории участников ООО «Литум» (ИНН 7805360880) — '
               '100% с 2022-07-29; (2) СПАРК-Интерфакс — управляющая компания (ИНН 6685028781) у заводов группы '
               '(ООО «ПСО Теплит» и др.) (вычитка m229).',
     'date': DAY},
    {'company_id': YE, 'decision': 'confirmed', 'inn': '7810943817',
     'reason': 'Предмет карточки g16540a36 (YE Russia). АО «ЮЕ Тех», до 06.08.2023 АО «ЮЕ-Интернейшнл», ИНН '
               '7810943817, ОГРН 1027804902344, Санкт-Петербург, пр-т Обуховской Обороны, 70, к. 3. Совпало: (1) '
               'api-fns egr — те же ИНН и ОГРН, генеральный директор 2015–ноябрь 2022 Пенни Юрье Мауно Олави '
               '(Финляндия) — по Castrén & Snellman, гендиректор и владелец 10% YE Russia; (2) tapki.com — АО «ЮЕ '
               'Тех», ИНН 7810943817, ОГРН 1027804902344, оптовая торговля электронным оборудованием (вычитка m229).',
     'date': DAY},
]


def get(obj, path):
    for k in path.split('.'):
        obj = (obj or {}).get(k)
    return obj


def put(obj, path, value):
    keys = path.split('.')
    for k in keys[:-1]:
        obj = obj.setdefault(k, {})
    if value is None:
        obj.pop(keys[-1], None)
    else:
        obj[keys[-1]] = value


RETRACT = ('buyer_name', 'seller', 'asset', 'sum', 'status')


def apply(data):
    """Возвращает число примененных правок; уже стоящее значение пропускается."""
    by = {d['id']: d for d in data['deals']}
    n = 0
    for cid, new in NEW_COMPANIES.items():
        if cid not in data['companies']:
            data['companies'][cid] = dict(new)
            n += 1
    for cid, field, old, new, quote, url in DEAL_EDITS:
        c = by[cid]
        cur = get(c, field)
        if cur == new:
            continue
        assert cur == old, (cid, field, cur)
        put(c, field, new)
        if field in RETRACT and old:
            c.setdefault('retracted', {}).setdefault(field, []).append(old)
        fact_edit_guard.log(c, field, new, quote, url, BY, DAY)
        n += 1
    for cid, field, old, new, quote, url in TEXT_EDITS:
        c = by[cid]
        cur = get(c, field) or ''
        if new in cur:
            continue
        assert cur.count(old) == 1, (cid, field)
        put(c, field, cur.replace(old, new))
        fact_edit_guard.log(c, field, get(c, field), quote, url, BY, DAY)
        n += 1
    for cid, role, old, new in NOTES:
        notes = by[cid].setdefault('accepted_notes', {}).setdefault('no_profile', {})
        cur = notes.get(role)
        if cur == new:
            continue
        assert (cur is None and old is None) or (old and cur and cur.startswith(old)), (cid, role, cur)
        if new is None:
            del notes[role]
        else:
            notes[role] = new
        n += 1
    return n


def registry(write):
    rows = json.load(open(REG, encoding='utf-8'))
    have = {r['company_id']: r for r in rows}
    todo = []
    for row in REGISTRY:
        cur = have.get(row['company_id'])
        if cur and cur.get('inn') == row['inn']:
            continue
        clash = [r['company_id'] for r in rows if r.get('inn') == row['inn'] and r['company_id'] != row['company_id']]
        assert not clash, (row['inn'], clash)
        todo.append(row)
    if write:
        for row in todo:
            if row['company_id'] in have:
                assert fns_notes_to_registry.edit_registry_entry(row['company_id'], row)
            else:
                rows = json.load(open(REG, encoding='utf-8'))
                rows.append(row)
                with open(REG, 'w', encoding='utf-8') as fh:
                    json.dump(rows, fh, ensure_ascii=False, indent=1)
    return len(todo)


def main(write):
    raw = open(DATA, encoding='utf-8').read()
    old, data = json.loads(raw), json.loads(raw)
    n = apply(data)
    if n:
        mass_edit_guard.check(old, data, os.environ.get('MASS_OK'))
    bad = fact_edit_guard.unbacked(old, data)
    assert not bad, bad
    r = registry(False)
    if not write:
        print('Сухой прогон: правок базы %d, записей реестра ИНН %d. Запись — с ключом --write.' % (n, r))
        return 0
    if n:
        fresh_raw = open(DATA, encoding='utf-8').read()
        fresh = json.loads(fresh_raw)
        apply(fresh)
        with open(DATA, 'w', encoding='utf-8') as f:
            f.write(json.dumps(fresh, ensure_ascii=False, indent=1) + ('\n' if fresh_raw.endswith('\n') else ''))
    registry(True)
    print('ЗАПИСАНО: правок базы %d, записей реестра ИНН %d.' % (n, r) if (n or r) else 'Уже применено.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv[1:]))
