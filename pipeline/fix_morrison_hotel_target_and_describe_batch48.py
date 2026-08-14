# -*- coding: utf-8 -*-
"""Сорок восьмая партия: испорченная ссылка target + падеж (Morrison
Hotel/Батурина) + 10 описаний.

НАЙДЕНО. У сделки g3d522ec0 («Продажа Еленой Батуриной отеля Morrison
Hotel в Дублине компании Zetland Capital») `target` указывал на профиль
g32050c9b «Еленой Батуриной» — саму продавщицу, да ещё в творительном
падеже (вырезано из заголовка без согласования). По тексту предмет
сделки — отель Morrison Hotel в Дублине, для которого в базе не было ни
одного профиля. Тот же класс, что Уфабурмаш/Делимобиль/Аэропорт
Оренбург (сторона вместо предмета) плюс падеж, не пропущенный через
casing.py (карточка 2021 года, до его появления).

ЧТО ДЕЛАЕТ.
1. Создаёт профиль «Morrison Hotel (Дублин)», переносит на него `target`
   сделки g3d522ec0.
2. Переименовывает g32050c9b из «Еленой Батуриной» (творительный) в
   «Елена Батурина» (именительный) и ставит его в `seller`/`seller_id`
   той же сделки — профиль человека не удаляется, просто занимает
   верную роль под верным именем.
3. Проставляет описания 10 профилям, прочитанным по своим единственным
   связанным сделкам.

Запуск:
    python3 pipeline/fix_morrison_hotel_target_and_describe_batch48.py            # сухой прогон
    python3 pipeline/fix_morrison_hotel_target_and_describe_batch48.py --write    # записать
"""
import hashlib
import json
import re
import sys

DATA = 'static/data/deals_promoted.json'
PLACEHOLDER = re.compile(r'^\s*(описание компании пока не добавлено'
                          r'|профиль сформирован по итогам чтения)', re.I)

DEAL_ID = 'g3d522ec0'
BATURINA_ID = 'g32050c9b'
BATURINA_OLD = 'Еленой Батуриной'
BATURINA_NEW = 'Елена Батурина'
HOTEL_SEED = 'Morrison Hotel (Дублин), Батурина, Zetland Capital 2021'
HOTEL_NAME = 'Morrison Hotel (Дублин)'
HOTEL_DESC = ('Бутик-отель на 145 номеров под брендом DoubleTree by '
              'Hilton; куплен Еленой Батуриной у ирландского NAMA в '
              '2012 году, в 2021-м продан Zetland Capital.')

DESCRIPTIONS = {
    'g9cd973e3': 'СП «Аэропортов регионов» Вексельберга и «Новапорт '
                 'Холдинга» Троценко; в 2021 году выиграло аукцион на '
                 'аэропорты Оренбурга и Орска за 3,193 млрд ₽.',
    'g99e35a0c': 'Образовательная платформа, выручка за 2025 год — 15 '
                 'млн ₽; в 2026 году привлекла 12,5 млн ₽ от Synergy '
                 'Ventures и brainbox_I.',
    'g3daf2d35': 'Структура Никиты Мазепина; в 2026 году купила 20% в '
                 'ИТ-стартапе «АрхиТех ИИ» за $15 млн.',
    'g57782a33': 'ТРЦ в Красногорске (Подмосковье), построен группой '
                 '«Регионов» Зелимхана Муцоева; выставлен на аукцион в '
                 '2023 году за 3,5 млрд ₽.',
    'ge46fa914': 'Оператор спутниковой и медиаинфраструктуры; в 2020 '
                 'году 100% акций у группы МТТ купил «Ростелеком».',
    'ga98270e6': 'ТРЦ в Тамбове площадью 35 тыс. кв. м; выставлен на '
                 'торги в 2018 году в рамках банкротства владельца.',
    'g79091b1d': 'Бизнес-центр в Красноярске (12 этажей, ~8000 кв. м); '
                 'продан с открытого аукциона в 2018 году за 425 млн ₽.',
    'g23e8efa9': 'Угольный разрез в Новокузнецке; в 2018 году продан на '
                 'банкротных торгах ГК «Южуралзолото».',
    'gd74c73c4': 'Зерновой оператор и парк зерновозов; в 2020 году '
                 'продан FESCO «Русагротрансу» (группа ВТБ) за 3,8 '
                 'млрд ₽.',
    'gc104790a': 'Приватизированный производитель грампластинок и '
                 'аудионосителей «Мелодия»; в 2020 году продан на '
                 'аукционе за 329,6 млн ₽.',
}


def new_id(seed, existing):
    cid = 'g' + hashlib.sha1(seed.encode('utf-8')).hexdigest()[:8]
    assert cid not in existing, 'коллизия id: %s' % cid
    return cid


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    comps = data['companies']
    by_id = {d['id']: d for d in data['deals']}

    deal = by_id[DEAL_ID]
    assert deal['target'] == BATURINA_ID, 'target сделки уже не Батурина'
    assert deal.get('seller') is None and deal.get('seller_id') is None, \
        'seller сделки уже заполнен'
    assert comps[BATURINA_ID]['name'] == BATURINA_OLD

    existing_ids = set(comps.keys())
    existing_names = {c.get('name') for c in comps.values()}
    assert HOTEL_NAME not in existing_names, 'имя нового профиля уже занято'
    assert BATURINA_NEW not in existing_names, 'имя уже занято'
    hid = new_id(HOTEL_SEED, existing_ids)
    print('НОВЫЙ ПРОФИЛЬ  %-12s %s' % (hid, HOTEL_NAME))
    print('ПЕРЕНОС TARGET  %s: %s -> %s' % (DEAL_ID, BATURINA_ID, hid))
    print('ПЕРЕИМЕНОВАНИЕ  %-12s %r -> %r' % (BATURINA_ID, BATURINA_OLD, BATURINA_NEW))
    print('SELLER  %s: -> %s (%s)' % (DEAL_ID, BATURINA_ID, BATURINA_NEW))

    if write:
        comps[hid] = {'name': HOTEL_NAME, 'ind': 'Недвижимость', 'desc': HOTEL_DESC}
        deal['target'] = hid
        deal['seller_id'] = BATURINA_ID
        deal['seller'] = BATURINA_NEW
        comps[BATURINA_ID]['name'] = BATURINA_NEW

    wrote, skipped = 0, []
    for cid, text in DESCRIPTIONS.items():
        c = comps.get(cid)
        assert c, 'профиля %s нет в базе' % cid
        assert 15 <= len(text) <= 220, 'описание %s вне 1–2 строк: %d' % (cid, len(text))
        old = str(c.get('desc') or '')
        if old.strip() == text:
            continue
        if old and not PLACEHOLDER.match(old):
            skipped.append((cid, c.get('name'), old[:60]))
            continue
        print('  ОПИСАНИЕ %-12s %-40s %s' % (cid, str(c.get('name'))[:40], text[:50]))
        if write:
            c['desc'] = text
        wrote += 1

    print('\nОписаний записано: %d' % wrote)
    if skipped:
        print('Пропущено (уже есть своё описание): %d' % len(skipped))
        for cid, name, old in skipped[:5]:
            print('   %s %s — %r' % (cid, name, old))

    real = sum(1 for v in comps.values()
               if (v.get('desc') or '').strip() and not PLACEHOLDER.match(str(v.get('desc'))))
    print('Всего профилей с описанием: %d из %d (%d%%)'
          % (real, len(comps), round(100 * real / len(comps))))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
