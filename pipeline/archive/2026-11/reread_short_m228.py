# -*- coding: utf-8 -*-
"""Вычитка 13 ноября 2026, партия m228 (короткая проверка, уход иностранных компаний 2022 года).

Доказательства (тексты — data/inbox/triage/sources_2026-11-12_m228.json):

g4c30b416 (Trafigura / «Восток Ойл»): по ЕГРЮЛ (OpenSanctions, набор «Russian Unified State Register
  of Legal Entities», ИНН 7727568649, ОГРН 1067746343708) «Восток Ойл» — ООО; CB Entreprises Sarl
  числилась участником с 10% с 30.04.2021 по 27.12.2022. Предмет и доля — долей в ООО. Заголовок
  без эпитета.
g373439fe (Electrolux): «Коммерсантъ» (5773590): «Владельцем ООО «Е.Кампани» с сентября 2022 года
  выступает Павел Потапов» — покупатель по имени, а не «местный менеджмент». Предмет — имя общества,
  описание уже в контексте.
g1def0d4f (Lindab): дата 2022-08-22 — день пресс-релиза; Lindab: «As of August 1, Lindab has no
  operations… Lindab's Russian subsidiary has been sold to the company's local Managing Director» —
  дня продажи нет, дата — годом.
g9e27d3f1 (Iveco / «АМТ»): ЕГРЮЛ (Датаньютон, ОГРН 1027400879890): 28.07.2022 вышла «ИВЕКО ГРУП Н.В.»
  (33,3%), доля перешла обществу ООО «Ивеко-АМТ»; 02.08.2022 общество переименовано в «АМТ Н.В.»;
  10.08.2022 ООО «АМТ» (ОГРН 1067415019495) — 100%. Дата — день выхода Iveco по реестру; покупатель —
  юрлицо, люди за ним — в контексте.
gab63a02f (X5 / Prisma): продавец по Интерфаксу и ТАСС — SOK Retail Int. Oy; юрконсультант SOK —
  Castrén & Snellman (castren.fi, кейс «SOK – Sale of Prisma Stores in St Petersburg»).
g660f4097 («Черкизово» / «Сибилла Рус»): сообщение Atria Plc 16.05.2022 (Nasdaq Helsinki, inderes.fi):
  «The sales price is approximately EUR 8 million» — цена раскрыта продавцом; юрконсультант Atria —
  Castrén & Snellman (castren.fi, «Atria – Sale of Sibylla Rus»).
gd77af086 (Helly Hansen): ЕГРЮЛ — из участников вышла «Хелли Хансен Россия АС» (Helly Hansen Russia AS),
  запись 13.09.2022 (Датаньютон, ОГРН 1137746670522); покупатель — ООО «Редиг».
g605d8d30 («Леста»): ЕГРЮЛ — 28.06.2022 вышла «Варгейминг Груп Лимитед» (100%), вошел Малик Хатажаев.
g5019c6ae (Electrolux Professional): значение стороны — с заглавной.
g47188b89 (Inchcape): PDF отчета за полугодие убран с сайта (404) — ссылка на копию в Wayback Machine.

    python3 pipeline/archive/2026-11/reread_short_m228.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY, DAY = 'reread_short_m228', '2026-11-13'

OS_VOSTOK = 'https://opensanctions.org/entities/ru-inn-7727568649'
Q_VOSTOK = ('LIMITED LIABILITY COMPANY VOSTOK OIL… Legal form LLC · Общества с ограниченной ответственностью '
            '(Russian Unified State Register of Legal Entities ru-inn-7727568649)… Ownership and Control: '
            'CB ENTREPRISES SARL - 10 2021-04-30 2022-12-27; NORD AXIS LTD - 10.00')
TRAF = 'https://www.trafigura.com/press-releases/trafigura-completes-the-exit-of-its-investment-in-vostok-oil/'
Q_TRAF = ('Trafigura’s shareholding in Vostok Oil, including the associated non-recourse bank debt, have been '
          'acquired by Nord Axis Limited… The transaction completed on 12 July 2022 for an undisclosed price.')
KOM_EL = 'https://kommersant.ru/doc/5773590'
Q_KOM_EL = ('Ранее это ООО принадлежало шведскому производителю крупной бытовой электроники Electrolux, который '
            'после начала военных действий на Украине продал свой российский бизнес локальному топ-менеджменту. '
            'Владельцем ООО «Е.Кампани» с сентября 2022 года выступает Павел Потапов')
LINDAB = 'https://news.cision.com/lindab/r/lindab-has-completed-the-exit-from-russia,c3617679'
Q_LINDAB = ('As of August 1, Lindab has no operations in, sales to, or purchases from Russia. As part of the exit '
            'process, Lindab\'s Russian subsidiary has been sold to the company\'s local Managing Director.')
DN_AMT = 'https://datanewton.ru/api/v2/history?ogrn=1027400879890&startDate=2000-01-01&attributes=OWNERS'
Q_AMT = ('ЕГРЮЛ, участники ООО «Ивеко-АМТ» (ИНН 7415019467): 2022-07-28 ИВЕКО ГРУП Н.В. 33.3% → нет, '
         'ООО «Ивеко-АМТ» (ИНН 7415019467) 33.3%; 2022-08-02 переименование в ООО «АМТ Н.В.»; 2022-08-10 '
         'ООО «АМТ» (ОГРН 1067415019495) 66.7% → 100.0%')
IFX_AMT = 'https://www.interfax.ru/business/898390'
IFX_X5 = 'https://www.interfax.ru/business/846496'
Q_X5 = ('X5 Retail Group договорилась с финским холдингом SOK Retail Int. OY… о приобретении у него компании, '
        'которая управляет супермаркетами, работавшими под брендом Prisma в Санкт-Петербурге')
CASTREN_SOK = 'https://www.castren.fi/cases/cases-2022/sok/'
Q_CASTREN_SOK = ('We advised Suomen Osuuskauppojen Keskuskunta when it sold the company responsible for St Petersburg '
                 'Prisma business to Russian X5 Group.')
ATRIA = 'https://www.inderes.fi/en/releases/atria-oyj-atria-sold-its-fast-food-business-in-russia'
Q_ATRIA = ('Atria has sold its fast food business Sibylla Rus LLC to Limited Liability Company Agricultural Complex '
           'Mikhailovskiy, which is part of the Cherkizovo Group. The sales price is approximately EUR 8 million.')
CASTREN_ATRIA = 'https://www.castren.fi/cases/atria-sale-of-sibylla-rus/'
Q_CASTREN_ATRIA = ('We advised Atria Plc in the sale of its Russian fast food business, Sibylla Rus LLC, to Limited '
                   'Liability Company Agricultural Complex Mikhailovskiy, which is part of the Cherkizovo Group.')
EGRUL = 'ЕГРЮЛ, история участников (pipeline/party_legal_names.py)'
Q_HH = ('ЕГРЮЛ, ООО «Ритейл РЦ» (бывш. «Хелли Хансен», ОГРН 1137746670522): 2022-09-13 участник '
        'КОМПАНИЯ С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ «ХЕЛЛИ ХАНСЕН РОССИЯ АС» 100% → нет; ООО «РЕДИГ» → 100%')
Q_LESTA = ('ЕГРЮЛ, ООО «Леста» (ИНН 7806038436): 2022-06-28 left ВАРГЕЙМИНГ ГРУП ЛИМИТЕД (100.0 → None); '
           '2022-06-28 joined Хатажаев Малик Атхамович (None → 100.0)')

# (id, поле, старое, новое, цитата, адрес)
EDITS = [
    ('g4c30b416', 'title', 'Гонконгская Nord Axis купила у Trafigura 10% «Восток Ойла»',
     'Nord Axis купил у Trafigura 10% «Восток Ойла»', Q_TRAF, TRAF),
    ('g4c30b416', 'asset', '10% проекта «Восток Ойл»', 'ООО «Восток Ойл»', Q_VOSTOK, OS_VOSTOK),
    ('g4c30b416', 'eco.share', '10% в проекте «Восток Ойл»', '10% доли в ООО «Восток Ойл»', Q_VOSTOK, OS_VOSTOK),
    ('g4c30b416', 'law.struct', 'Долей владела швейцарская CB Enterprises Sarl; покупатель — Nord Axis Limited (Гонконг).',
     'Долей владела швейцарская CB Enterprises Sarl; покупатель — Nord Axis Limited (Гонконг). По ЕГРЮЛ '
     'CB Enterprises Sarl числилась участником ООО «Восток Ойл» с 10% до 27 декабря 2022 года.', Q_VOSTOK, OS_VOSTOK),

    ('g373439fe', 'asset', 'ООО «Е.Кампани» — российская дочерняя компания шведского производителя техники',
     'ООО «Е.Кампани»', Q_KOM_EL, KOM_EL),
    ('g373439fe', 'eco.share', 'Российская дочерняя компания Electrolux — ООО «Е.Кампани»',
     'Доля в ООО «Е.Кампани»', Q_KOM_EL, KOM_EL),
    ('g373439fe', 'buyer_name', 'Местный менеджмент (владелец — Павел Потапов)', 'Павел Потапов', Q_KOM_EL, KOM_EL),
    ('g373439fe', 'title', 'Местный менеджмент купил российский бизнес Electrolux',
     'Павел Потапов купил российскую компанию Electrolux', Q_KOM_EL, KOM_EL),

    ('g1def0d4f', 'date', '2022-08-22', '2022', Q_LINDAB, LINDAB),
    ('g1def0d4f', 'title', 'Управляющий директор российской «дочки» Lindab купил ее у шведской группы',
     'Местный управляющий директор купил российскую компанию Lindab', Q_LINDAB, LINDAB),

    ('g9e27d3f1', 'date', '2022-07-13', '2022-07-28', Q_AMT, DN_AMT),
    ('g9e27d3f1', 'buyer_name', 'ООО «АМТ» (Владимир и Андрей Новики)', 'ООО «АМТ»', Q_AMT, DN_AMT),
    ('g9e27d3f1', 'asset', '33,3% совместного предприятия «АМТ-Ивеко» в Миассе', 'ООО «Ивеко-АМТ»', Q_AMT, DN_AMT),
    ('g9e27d3f1', 'eco.share', '33,3% в совместном предприятии «АМТ-Ивеко» (ныне ООО «АМТ Н.В.»)',
     '33,3% доли в ООО «Ивеко-АМТ»', Q_AMT, DN_AMT),
    ('g9e27d3f1', 'title', 'Компания «АМТ» купила у Iveco 33,3% совместного завода грузовиков в Миассе',
     '«АМТ» купил у Iveco 33,3% завода «Ивеко-АМТ» в Миассе', Q_AMT, DN_AMT),
    ('g9e27d3f1', 'law.struct',
     'Доля Iveco перешла к российскому совладельцу — ООО «АМТ», которое теперь владеет 100% ООО «АМТ Н.В.».',
     'По ЕГРЮЛ Iveco Group N.V. вышла из ООО «Ивеко-АМТ» 28 июля 2022 года, ее 33,3% перешли самому обществу; '
     '2 августа 2022 года общество переименовано в ООО «АМТ Н.В.», 10 августа ООО «АМТ» стало владельцем 100%.',
     Q_AMT, DN_AMT),

    ('gab63a02f', 'seller', 'SOK (S Group)', 'SOK Retail Int. Oy', Q_X5, IFX_X5),
    ('gab63a02f', 'eco.share', '—', 'Доля в ООО «Призма»', Q_X5, IFX_X5),
    ('gab63a02f', 'title', 'X5 купила у финской SOK петербургские супермаркеты Prisma',
     'X5 купила у SOK петербургские супермаркеты Prisma', Q_X5, IFX_X5),
    ('gab63a02f', 'law.adv',
     [['Стороны сделки', 'Не раскрывались', 'Юридические консультанты в публичных источниках не раскрывались']],
     [['Юридический консультант продавца (SOK)', 'Castrén & Snellman',
       'Продажа компании, которая вела петербургский бизнес Prisma, группе X5. Микко Ханни, Паулийна Тенхунен. '
       'Источник: castren.fi']], Q_CASTREN_SOK, CASTREN_SOK),

    ('g660f4097', 'sum', 'Не раскрыта', '≈8 млн €', Q_ATRIA, ATRIA),
    ('g660f4097', 'eco.sum', 'Не раскрыта', '≈8 млн €', Q_ATRIA, ATRIA),
    ('g660f4097', 'title', '«Черкизово» купило у финской Atria поставщика фастфуда «Сибилла Рус»',
     '«Черкизово» купило у Atria «Сибилла Рус»', Q_ATRIA, ATRIA),
    ('g660f4097', 'law.adv',
     [['Стороны сделки', 'Не раскрывались', 'Юридические консультанты в публичных источниках не раскрывались']],
     [['Юридический консультант продавца (Atria)', 'Castrén & Snellman',
       'Продажа ООО «Сибилла Рус» ООО «АПК «Михайловский»» из группы «Черкизово». Микко Ханни. Источник: castren.fi']],
     Q_CASTREN_ATRIA, CASTREN_ATRIA),

    ('gd77af086', 'seller', 'Helly Hansen (Canadian Tire)', 'Helly Hansen Russia AS', Q_HH,
     'https://datanewton.ru/api/v2/history?ogrn=1137746670522&startDate=2000-01-01&attributes=OWNERS'),
    ('gd77af086', 'title', 'Гендиректор и юрист российской Helly Hansen купили компанию у Canadian Tire',
     '«Редиг» купил российскую компанию Helly Hansen', Q_HH,
     'https://datanewton.ru/api/v2/history?ogrn=1137746670522&startDate=2000-01-01&attributes=OWNERS'),

    ('g605d8d30', 'seller', 'Wargaming', 'Wargaming Group Limited', Q_LESTA, EGRUL),

    ('g5019c6ae', 'buyer_name', 'местный менеджмент', 'Местный менеджмент',
     'Electrolux Professional has decided to cease operations in Russia and divest its business in the country '
     'to local management', 'https://interfax.com/newsroom/top-stories/81141/'),
]
RETRACT = {('gab63a02f', 'seller'), ('gd77af086', 'seller'), ('g9e27d3f1', 'date'), ('g1def0d4f', 'date')}
DATE_BASIS = {'g9e27d3f1': 'registry', 'gd77af086': 'registry', 'g605d8d30': 'registry'}
SUM_BASIS = {'g660f4097': 'disclosed'}
SRC = {
    'g4c30b416': [['OpenSanctions (ЕГРЮЛ)', OS_VOSTOK]],
    'gab63a02f': [['Castrén & Snellman', CASTREN_SOK]],
    'g660f4097': [['Atria (сообщение для биржи)', ATRIA], ['Castrén & Snellman', CASTREN_ATRIA]],
    'g9e27d3f1': [['Датаньютон (ЕГРЮЛ)', DN_AMT]],
}
INCH_OLD = 'https://www.inchcape.com/wp-content/uploads/2022/07/Inchcape-1H22-RNS-FINAL61.pdf'
INCH_NEW = ('http://web.archive.org/web/20240626070250/https://www.inchcape.com/wp-content/uploads/2022/07/'
            'Inchcape-1H22-RNS-FINAL61.pdf')
# Отчет Inchcape за полугодие 2022 года с сайта компании убран (404 на 13.11.2026) — ссылка на копию в Wayback.
REPLACE_SRC = {'g47188b89': (INCH_OLD, INCH_NEW)}
NOTES = {
    ('g9e27d3f1', 'target'): 'ООО «АМТ Н.В.» (до 2 августа 2022 года — ООО «Ивеко-АМТ»), ИНН 7415019467, ОГРН '
                             '1027400879890 — по истории участников Датаньютона; профиль не заводили.',
    ('g9e27d3f1', 'buyer'): 'ООО «АМТ», ОГРН 1067415019495 (история участников ООО «АМТ Н.В.», Датаньютон); '
                            'владельцы — Владимир (80%) и Андрей (20%) Новики (Интерфакс). Профиль не заводили.',
    ('gd77af086', 'seller'): 'Продавец — норвежская Helly Hansen Russia AS из группы Canadian Tire, российского '
                             'юрлица-продавца нет. История участников ЕГРЮЛ (datanewton, ОГРН 1137746670522): 100% у '
                             'Helly Hansen Russia AS до 13.09.2022, затем у ООО «Редиг».',
}


def _get(c, f):
    if '.' in f:
        h, t = f.split('.', 1)
        return (c.get(h) or {}).get(t)
    return c.get(f)


def _set(c, f, v):
    if '.' in f:
        h, t = f.split('.', 1)
        c.setdefault(h, {})[t] = v
    else:
        c[f] = v


def apply(data):
    by = {d['id']: d for d in data['deals']}
    n = 0
    for cid, f, old, new, quote, url in EDITS:
        c = by[cid]
        cur = _get(c, f)
        if cur == new:
            continue
        assert cur == old, (cid, f, cur)
        _set(c, f, new)
        if (cid, f) in RETRACT:
            c.setdefault('retracted', {}).setdefault(f, []).append(old)
        if f in fact_edit_guard.FACT_FIELDS:
            fact_edit_guard.log(c, f, new, quote, url, BY, DAY)
        n += 1
    for cid, v in DATE_BASIS.items():
        if by[cid].get('date_basis') != v:
            by[cid]['date_basis'] = v
            n += 1
    for cid, v in SUM_BASIS.items():
        if by[cid].get('sum_basis') != v:
            by[cid]['sum_basis'] = v
            n += 1
    for cid, rows in SRC.items():
        have = {s[1] for s in by[cid].get('src') or []}
        for r in rows:
            if r[1] not in have:
                by[cid].setdefault('src', []).append(list(r))
                n += 1
    for cid, (o, nw) in REPLACE_SRC.items():
        for s in by[cid].get('src') or []:
            if s[1] == o:
                s[1] = nw
                n += 1
    for (cid, role), text in NOTES.items():
        nb = by[cid].setdefault('accepted_notes', {}).setdefault('no_profile', {})
        if nb.get(role) != text:
            nb[role] = text
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
