# -*- coding: utf-8 -*-
"""Вычитка, марафон 12 ноября 2026, партия m226 (часть b): три лота «Дом.РФ» и «Вымпелкома».

Чего не умеет review.py: снятие «начальная цена» из суммы и замена ее точной цифрой извещения,
снятие поля до «—», правка этапа events[]. Проза разделов — write_card.py (w/*_wr.json).

gbcf07c78 (часть доходного дома Хомяковых, «Вымпелком»): начальная цена — 1,05 млрд ₽ (CNews со
  слов Российского аукционного дома; РИА — «немногим более 1 миллиарда»); eco.val повторял сумму
  и минимальную цену из law.struct — снят; предмет — с именем дома.
g96d69d52 (Солодежня, Псков): eco.rationale был не мотивом сделки, а пересказом условий и истории
  здания (они перенесены в eco.context и law.terms) — снят до «—»; предмет — с адресом.
ga8d7e0ee (дом купца Комлина, Сыктывкар): заголовок по стандарту торгов; предмет — с адресом
  (Кирова, 33 — Комиинформ); еще два источника.

    python3 pipeline/archive/2026-11/reread_oneoff_m226b.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY, DAY = 'reread_oneoff_m226b', '2026-11-12'


CN = 'https://www.cnews.ru/news/top/2026-10-05_bilajn_prodaet_svoj_ofis'
Q_CN = ('Российский аукционный дом (РАД) сообщил о выставлении на торги принадлежащего «Вымпелкому» (торговая марка '
        '«Билайн») офисного здания в центре Москвы. Торги пройдут 21 октября 2026 г. на электронной торговой площадке '
        'lot-online.ru. Начальная цена лота составляет 1,05 млрд руб..')
RB = 'https://realty.ria.ru/20261002/bilajn-2121696879.html'
Q_RB = ('лот представляет собой часть офисного здания класса В по адресу: улица 1-я Тверская-Ямская, 2, строение 1 '
        '(бывший доходный дом братьев Хомяковых). На продажу выставлены помещения на мансардном и первом-четвертом '
        'этажах суммарно на 2,9 тысячи квадратных метров')
RP = 'https://realty.ria.ru/20261002/pskov-2121718869.html'
Q_RP = ('в составе лота - двухэтажное здание площадью 500,2 квадратного метра (улица Гоголя, 42) и аренда участка '
        'площадью 0,34 гектара.')
RS = 'https://realty.ria.ru/20261002/syktyvkar-2121760598.html'
KM = 'https://komiinform.ru/news/301784'
Q_KM = ('"Дом.РФ" проведет конкурс по продаже объекта культурного наследия регионального значения - деревянного '
        'двухэтажного дома купца Василия Петровича Комлина в центральной части Сыктывкара (улица Кирова, 33). '
        'Продается здание площадью 665,3 квадратного метра и аренда участка 0,12 гектара.')

EDITS = [
    ('gbcf07c78', 'sum', '1 млрд ₽ (начальная цена, торги на понижение)', '1,05 млрд ₽', Q_CN, CN),
    ('gbcf07c78', 'eco.sum', '1 млрд ₽ (начальная цена, торги на понижение)', '1,05 млрд ₽', Q_CN, CN),
    ('gbcf07c78', 'eco.val', 'Стартовая цена лота — 1,05 млрд ₽. Торги голландские: цена идет на понижение, но не ниже '
     '735 млн ₽.', '—', 'повтор суммы и минимальной цены из law.struct', CN),
    ('gbcf07c78', 'asset', 'часть офисного здания на 1-й Тверской-Ямской ул. в Москве: 2,9 тыс. кв. м (29% площади здания)',
     'Часть бывшего доходного дома Хомяковых на 1-й Тверской-Ямской, 2, стр. 1 в Москве: 2,9 тыс. кв. м', Q_RB, RB),
    ('g96d69d52', 'eco.rationale',
     'Торги организует Фонд инвестиционного развития Псковской области, лот размещен на сайте земля.дом.рф. Собственник '
     'обязан завершить работы по сохранению объекта культурного наследия федерального значения до июля 2029 года. '
     'Утрачены древняя кровля, изразцовые печи, дверные и оконные заполнения; до революции здание служило богатыми '
     'жилыми палатами, а в XIX веке купец Степан Воронин использовал его для изготовления и хранения солода — отсюда '
     'название «Солодежня».', '—', 'не мотив сделки: условия и история здания — в eco.context и law.terms', RP),
    ('g96d69d52', 'asset', 'здание солодежни XVII века в Пскове: 500,2 кв. м, аренда участка 0,34 га',
     'Солодежня на улице Гоголя, 42 в Пскове: 500,2 кв. м, аренда участка 0,34 га', Q_RP, RP),
    ('ga8d7e0ee', 'title', '«Дом.РФ» продает купеческий особняк начала XX века в Сыктывкаре',
     '«Дом.РФ» выставил на торги дом купца Комлина в Сыктывкаре', Q_KM, KM),
    ('ga8d7e0ee', 'asset', 'дом купца В. П. Комлина в Сыктывкаре (Республика Коми): 665,3 кв. м, аренда участка 0,12 га',
     'Дом купца Комлина на улице Кирова, 33 в Сыктывкаре: 665,3 кв. м, аренда участка 0,12 га', Q_KM, KM),
]
SRC_TAIL = {
    'ga8d7e0ee': [['Комиинформ', KM], ['pg11.ru', 'https://pg11.ru/news/151793']],
}
SRC = {}
SELLER = {}
EVENTS = {
    'gbcf07c78': ('2026-10-02', '2026-10-02', 'Торги объявлены',
                  'Голландский аукцион назначен на 21 октября 2026 года: стартовая цена — 1,05 млрд ₽, нижняя '
                  'граница — 735 млн ₽.', ['CNews', CN]),
}
NO_PROFILE_SELLER = {}

def get(c, f):
    if '.' in f:
        a, b = f.split('.')
        return (c.get(a) or {}).get(b)
    return c.get(f)


def put(c, f, v):
    if '.' in f:
        a, b = f.split('.')
        c.setdefault(a, {})[b] = v
    else:
        c[f] = v


def apply(data):
    by = {d['id']: d for d in data['deals']}
    n = 0
    for cid, f, old, new, quote, url in EDITS:
        c = by[cid]
        if get(c, f) == new:
            continue
        assert get(c, f) == old, (cid, f, get(c, f))
        put(c, f, new)
        fact_edit_guard.log(c, f, new, quote, url, BY, DAY)
        n += 1
    for cid, srcs in SRC.items():
        c = by[cid]
        have = [s[1] for s in c['src']]
        add = [s for s in srcs if s[1] not in have]
        if add:
            c['src'] = add + c['src']
            n += 1
    for cid, (old, new, sid, quote, url) in SELLER.items():
        c = by[cid]
        if c.get('seller') == new:
            continue
        assert c.get('seller') == old and not c.get('seller_id'), (cid, c.get('seller'))
        c['seller'] = new
        if sid:
            c['seller_id'] = sid
            (c.get('accepted_notes') or {}).get('no_profile', {}).pop('seller', None)
        else:
            c.setdefault('accepted_notes', {}).setdefault('no_profile', {})['seller'] = NO_PROFILE_SELLER[cid]
        c.setdefault('retracted', {}).setdefault('seller', []).append(old)
        for pe in (c.get('party_evidence') or {}).get('seller') or []:
            if pe.get('value') == old:
                pe['value'], pe['url'] = new, url
        fact_edit_guard.log(c, 'seller', new, quote, url, BY, DAY)
        n += 1
    for cid, srcs in SRC_TAIL.items():
        c = by[cid]
        have = [s[1] for s in c['src']]
        add = [s for s in srcs if s[1] not in have]
        if add:
            c['src'] = c['src'] + add
            n += 1
    for cid, (old, new, title, note, src) in EVENTS.items():
        c = by[cid]
        e = c['events'][0]
        if e['date'] == new and e['note'] == note:
            continue
        assert e['date'] == old, (cid, e)
        e.update({'date': new, 'title': title, 'note': note, 'source': src})
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
    sys.exit(main('--write' in sys.argv[1:]))
