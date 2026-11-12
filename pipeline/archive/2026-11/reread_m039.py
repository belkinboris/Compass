# -*- coding: utf-8 -*-
"""Вычитка, партия m039 (марафон 12 ноября 2026): правки, которые не ложатся в review.py.

Что здесь и почему не через таблицу FIXES:
  * сумма «Не раскрыта» (review.py ее не принимает) — со снятым значением в retracted.sum;
  * дата годом или днем из истории участников ЕГРЮЛ (review.py год не меняет, день берет
    только из слов статьи);
  * поле прозы, которое сводится к «—» (цели сделки в статье нет; «показатели» — не финансы);
  * смена стороны на профиль, которого нет в базе (новый профиль), и тексты профилей;
  * отрасль карточки и профиля предмета (классификация по предмету сделки, не факт статьи).
Каждая правка факта подтверждена fact_edit_guard.log(...) цитатой статьи или реестра.
Для поля, у которого были записи таблицы правок, их отпечатки кладутся в proofread_absorbed.

    python3 pipeline/archive/2026-11/reread_m039.py            # сухой прогон
    python3 pipeline/archive/2026-11/reread_m039.py --write    # запись (повтор — «уже применено»)
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY, DAY = 'reread_m039', '2026-11-12'

# (карточка, поле, было, стало, цитата, адрес). Поле — путь через точку; «стало» None — снять ключ.
EDITS = []
# Новые профили: id -> профиль (id выбран accept_card._new_profile_id по имени).
NEW_PROFILES = {}
# Тексты профилей: (id, ключ, было, стало).
PROFILE_EDITS = []
# Снятые значения: (карточка, поле, значение) — в card['retracted'][поле].
RETRACT = []
FACT_FIELDS = ('title', 'date', 'status', 'sum', 'eco.sum', 'eco.share', 'buyer', 'buyer_name', 'seller',
               'seller_id', 'target', 'asset', 'asset_id', 'law.adv', 'eco.finadv')

# --- часть 1: gd75ae46f, g44fc5b69, gc9a9d929, g737a0487, g573b8819, g97d9fa60 ---
_V23 = 'https://www.vedomosti.ru/realty/articles/2023/04/06/969709-metropolis-smenil-vladeltsa'
_V24 = 'https://www.vedomosti.ru/realty/articles/2024/07/10/1049033-tps-nedvizhimost-vzyala-v-upravlenie-metropolis'
EDITS += [
    ('gd75ae46f', 'sum', '30–35 млрд ₽ (предполагаемая)', 'Не раскрыта',
     'Сумму сделки представитель Balchug Capital конкретизировать отказался, сообщив лишь, что цена была «привлекательной».', _V23),
    ('gd75ae46f', 'eco.sum', '30–35 млрд ₽ (предполагаемая)', 'Не раскрыта',
     'Сумму сделки представитель Balchug Capital конкретизировать отказался, сообщив лишь, что цена была «привлекательной».', _V23),
    ('gd75ae46f', 'date', '2023-04-06', '2023',
     'В Balchug Capital, которая с апреля 2023 г. владеет «Метрополисом», подтвердили (день перехода в статьях не назван; 6 апреля 2023 — день публикации)', _V24),
    ('gd75ae46f', 'eco.rationale', '«Метрополис» — один из самых посещаемых ТРЦ Москвы. Его построил казахстанский девелопер Capital Partners в 2009 году и через несколько лет продал фонду Morgan Stanley за $1,2 млрд; для российского рынка недвижимости это был тогда рекорд. Позднее половину комплекса купил фонд американского девелопера Hines.', '—', '', ''),
]
RETRACT += [('gd75ae46f', 'sum', '30–35 млрд ₽ (предполагаемая)')]

_K44 = 'https://www.kommersant.ru/doc/7478323'
_REG44 = 'https://datanewton.ru/api/v2/history?ogrn=1137847507490&startDate=2000-01-01&attributes=OWNERS'
NEW_PROFILES['ge9337382'] = {
    'name': 'ГК ЗОЖ', 'ind': 'Холдинги', 'legal_short': 'АО «ГК ЗОЖ»',
    'desc': 'Холдинг гендиректора ГК «Черноголовка» Алексея Четвергова: производители спортивного питания «Прайм-Крафт» и «Беркана» (Cybermass).',
    'kpi': ['Профиль', 'Автоматический']}
EDITS += [
    ('g44fc5b69', 'buyer', 'g5ff0a3de', 'ge9337382',
     'АО ГК ЗОЖ стало единственным владельцем ООО «Беркана», обнаружил “Ъ” в базе СПАРК. Гендиректором ГК ЗОЖ выступает Алексей Четвергов', _K44),
    ('g44fc5b69', 'date', '2024', '2024-09-12',
     '2024-09-12: Участники — выбыл: БОГДАНОВ АНДРЕЙ АНДРЕЕВИЧ (ИНН: 780600847590) 100.0%; (10 000 руб.).', _REG44),
]
PROFILE_EDITS += [
    ('g4480ebb8', 'desc', 'Производитель спортивного питания под брендом Cybermass, топ-15 рынка с долей 7%; в 2024 году ее 100% купила ГК «Черноголовка» за 250–300 млн ₽ (по оценке).',
     'Производитель спортивного питания под брендом Cybermass: протеиновые продукты, добавки и витамины.'),
]

_K32 = 'https://www.kommersant.ru/doc/7851711'
EDITS += [
    ('gc9a9d929', 'date', '2024', '2025',
     'В начале 2025 года компания стала владельцем бренда «Полугар», выкупив его у главного винокура и технолога компании «Родионов с сыновьями» Ильи Родионова.', _K32),
    ('gc9a9d929', 'eco.target_fin', 'Гильдия «Алкопро» ставит «Полугар» на шестое место по продажам. Весь рынок зерновых дистиллятов в России за 2024 год, по данным агентства «ЭТА.Лаб», — свыше 54 тыс. дал.', '—', '', ''),
]
PROFILE_EDITS += [
    ('g84f11948', 'desc', 'В 2024 году купила бренд зернового дистиллята «Полугар» и планирует развивать его продажи и маркетинг.',
     'Импортер и дистрибутор алкоголя; выпускает водку Tchaikovsky, джин Lockwood и коньяк «Айвазовский».'),
    ('g701d1e63', 'desc', 'Бренд зернового дистиллята; в 2024 году его купила Luding Group.',
     'Марка зернового дистиллята («хлебного вина»); с 2025 года принадлежит Luding Group.'),
]

_V737 = 'https://www.vedomosti.ru/realty/articles/2024/12/11/1080608-inter-rao-vozmozhno-nashla-novoe-mesto-dlya-razmescheniya-shtab-kvartiri'
EDITS += [
    ('g737a0487', 'date', '2024-12-11', '2024',
     'Энергетический холдинг « Интер РАО » выкупил у девелопера Sminex часть делового квартала «Московский шелк» (день сделки не назван; 11 декабря 2024 — день публикации)', _V737),
    ('g737a0487', 'ind', 'Энергетика', 'Недвижимость', '', ''),
]
PROFILE_EDITS += [
    ('g8451d088', 'ind', 'Энергетика', 'Недвижимость'),
    ('g8451d088', 'desc', 'Бизнес-центр площадью 18,2 тыс. кв. м в деловом квартале «Московский шелк» в Хамовниках; в 2024 году его у Sminex купил «Интер РАО», планируя перевести туда штаб-квартиру холдинга.',
     'Бизнес-центр площадью 18,2 тыс. кв. м в деловом квартале «Московский шелк» на Саввинской набережной в Хамовниках.'),
]

_RU21 = 'https://ufa.rbc.ru/ufa/21/02/2025/67b81fd99a79475dee0e2962'
_RU18 = 'https://ufa.rbc.ru/ufa/18/02/2025/67b463819a7947ae71ed05ee'
EDITS += [
    ('g573b8819', 'date', '2024', '2025',
     'Группа Accent ищет нового покупателя на складской комплекс «Сигма» в Уфе. 21 февраля 2025: Сделка по продаже складского комплекса «Сигма» в Уфе инвестиционной компании «Парус Управление Активами» (Parus Asset Management) не состоялась.', _RU21),
    ('g573b8819', 'seller_id', 'g985fe66e', None,
     'Компанией владеют Артур Хазигалеев, Марат Фаттахов, Марат Ахметшин и Александр Самонов.', _RU18),
    ('g573b8819', 'seller', 'Группа Accent', 'Александр Самонов, Артур Хазигалеев, Марат Фаттахов и Марат Ахметшин',
     'Компанией владеют Артур Хазигалеев, Марат Фаттахов, Марат Ахметшин и Александр Самонов.', _RU18),
]
PROFILE_EDITS += [
    ('g862f7df1', 'desc', 'Владеет логопарком «Сигма» в Уфе (85 тыс. кв. м); в 2024 году его купила Parus Asset Management у группы Accent Александра Самонова.',
     'Владелец логопарка «Сигма» класса «А» в Уфе (78,6 тыс. кв. м).'),
    ('gb998e33c', 'desc', 'Девелопер (Central Properties); в 2024 году купил логопарк «Сигма» в Уфе (85 тыс. кв. м) у группы Accent основателя сети «Копейка» Александра Самонова.',
     'Управляющая компания паевых фондов недвижимости (ООО «Парус Управление Активами»): складские комплексы, офисы и торговые центры.'),
]

EDITS += [
    ('g97d9fa60', 'eco.target_fin', 'Все активы «Агро-Белогорья» находятся в Белгородской области. Это 20 свинокомплексов, три комбикормовых завода, мясопереработка и земельный банк.', '—', '', ''),
]
EDITS += [
    ('g44fc5b69', 'title', 'ГК «Черноголовка» купила производителя спортивного питания Cybermass (ООО «Беркана»)',
     'ГК ЗОЖ купила ООО «Беркана»',
     'АО ГК ЗОЖ стало единственным владельцем ООО «Беркана», обнаружил “Ъ” в базе СПАРК.', _K44),
]




def get(card, path):
    cur = card
    for p in path.split('.'):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(p)
    return cur


def put(card, path, value):
    parts = path.split('.')
    cur = card
    for p in parts[:-1]:
        cur = cur.setdefault(p, {})
    if value is None:
        cur.pop(parts[-1], None)
    else:
        cur[parts[-1]] = value


def apply(data, report):
    import review
    fixes = review.load_fixes()
    by = {d['id']: d for d in data['deals']}
    comps = data['companies']
    for cid, prof in NEW_PROFILES.items():
        if cid in comps:
            report.append('профиль %s уже есть' % cid)
        else:
            comps[cid] = prof
            report.append('новый профиль %s %s' % (cid, prof['name']))
    for cid, key, old, new in PROFILE_EDITS:
        cur = comps[cid].get(key)
        if cur == new:
            report.append('уже применено: профиль %s.%s' % (cid, key))
            continue
        assert cur == old, (cid, key, cur)
        if new is None:
            comps[cid].pop(key, None)
        else:
            comps[cid][key] = new
        report.append('профиль %s.%s' % (cid, key))
    for cid, field, old, new, quote, url in EDITS:
        card = by[cid]
        cur = get(card, field)
        if cur == new:
            report.append('уже применено: %s %s' % (cid, field))
            continue
        assert cur == old, (cid, field, cur)
        put(card, field, new)
        if field in FACT_FIELDS or field == 'eco.share':
            fact_edit_guard.log(card, field, new, quote, url, BY, DAY)
        absorbed = card.setdefault('proofread_absorbed', {})
        for r in fixes:
            if r.get('id') == cid and r.get('field') == field and r.get('new') is not None \
                    and r.get('new') != new:
                fp = review.fix_fingerprint(r['new'])
                lst = absorbed.setdefault(field, [])
                if fp not in lst:
                    lst.append(fp)
        if not absorbed:
            card.pop('proofread_absorbed', None)
        report.append('%s %s: %r → %r' % (cid, field, str(old)[:50], str(new)[:50]))
    for cid, field, value in RETRACT:
        lst = by[cid].setdefault('retracted', {}).setdefault(field, [])
        if value not in lst:
            lst.append(value)


def main(write):
    raw = open(DATA, encoding='utf-8').read()
    old, data = json.loads(raw), json.loads(raw)
    report = []
    apply(data, report)
    print('\n'.join(report))
    mass_edit_guard.check(old, data, os.environ.get('MASS_OK'))
    bad = fact_edit_guard.unbacked(old, data)
    assert not bad, bad
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    fresh_raw = open(DATA, encoding='utf-8').read()
    fresh = json.loads(fresh_raw)
    apply(fresh, [])
    with open(DATA, 'w', encoding='utf-8') as f:
        f.write(json.dumps(fresh, ensure_ascii=False, indent=1) + ('\n' if fresh_raw.endswith('\n') else ''))
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv[1:]))
