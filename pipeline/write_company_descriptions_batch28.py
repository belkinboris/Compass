# -*- coding: utf-8 -*-
"""Двадцать восьмая партия: 8 описаний + карточка `g52730430`, где
покупатель был записан предметом сделки — известный, но неизмеренный
класс дефекта из CLAUDE.md («Обратный случай (предметом стоит
покупатель) правилом не ловится... класс находится чтением»).

ДЕФЕКТ. Сделка `g52730430` («Продажа дачи принца Ольденбургского на
Каменном острове — АО «Легион»», 2019 год) несла `buyer: null` и
`target: gba35c8d8` — профиль с именем «Легион». Но по тексту победителем
аукциона (то есть ПОКУПАТЕЛЕМ) стало именно АО «Легион», а предмет
сделки — сама дача (памятник архитектуры на Каменном острове), которую
профиль «Легион» не называет вовсе. Профиль `gba35c8d8` при этом
корректно используется как `target` в ДРУГОЙ сделке (`g8fb922a6`,
Siemens продал бизнес-центр «Легион II» — актив так и называется) —
трогать его нельзя. Заведены два новых профиля: покупатель (АО «Легион»,
СПВ, зарегистрировано в августе 2019 года специально под этот аукцион —
общей сущности со зданием «Легион II» в источнике не названо, id и имя
проверены на отсутствие коллизии) и сам предмет (дача). Сделка 2019 года
не показывается на сайте (`SITE_MIN_YEAR=2022`), но это база данных, а
не только витрина — роль сторон обязана быть верной независимо от того,
видна ли карточка сейчас.

ЧТО ДЕЛАЕТ. 8 описаний, 2 новых профиля, 1 правка ролей одной сделки.

Запуск:
    python3 pipeline/write_company_descriptions_batch28.py            # сухой прогон
    python3 pipeline/write_company_descriptions_batch28.py --write    # записать
"""
import json
import re
import sys

DATA = 'static/data/deals_promoted.json'
PLACEHOLDER = re.compile(r'^\s*(описание компании пока не добавлено'
                          r'|профиль сформирован по итогам чтения)', re.I)

NEW_BUYER_ID = 'g2046c2ed'
NEW_BUYER = {
    'name': 'АО «Легион» (Каменный остров)',
    'ind': 'Недвижимость',
    'desc': 'Компания, зарегистрированная в августе 2019 года; в том же '
            'году выиграла аукцион Дом.РФ на памятник архитектуры на '
            'Каменном острове в Санкт-Петербурге.',
    'kpi': ['Профиль', 'Автоматический'],
}
NEW_TARGET_ID = 'ga775fa77'
NEW_TARGET = {
    'name': 'Дача принца Ольденбургского (дача Долгорукова)',
    'ind': 'Недвижимость',
    'desc': 'Памятник деревянной архитектуры федерального значения '
            '(1831–1833, арх. Смарагд Шустов) на Каменном острове в '
            'Санкт-Петербурге, 1613 кв. м.',
    'kpi': ['Профиль', 'Автоматический'],
}

DESCRIPTIONS = {
    'gdccff9b3': 'Структура госкорпорации «Росатом» для сделок в '
                 'электронике и микроэлектронике; купила 50% Kraftway, '
                 'вела переговоры о покупке разработчика процессоров '
                 '«Эльбрус» (МЦСТ).',
    'gd28693f6': 'Владелец золотодобывающих участков «Гурбей» и '
                 '«Светино» в Иркутской области; в 2023 году продан '
                 'структурами Ростеха компании «ИГ Геоинвест».',
    'gce487d25': 'Лискинский маслоэкстракционный завод в Воронежской '
                 'области, производит нерафинированное растительное '
                 'масло и подсолнечный шрот.',
    'gc4b5b9a8': 'Сельскохозяйственное предприятие с земельным банком '
                 '188 тыс. га в Забайкальском крае.',
    'gb7d607ba': 'Торгово-выставочный комплекс «Тишинка» в Москве '
                 '(22 500 кв. м), построен в 1996 году на месте '
                 'Тишинского рынка; в 2022–2023 годах полностью выкуплен '
                 'Capital Group под жилую застройку.',
    'g17451b4f': 'Управляющая компания pre-IPO фондов; в 2024 году '
                 'вложилась в сервис аренды жилья «Суточно.ру», выкупив '
                 '16,03% у основателя.',
    'g08f2a986': 'Строительный холдинг, скупает в России заводы '
                 'стройматериалов ушедших иностранных производителей — '
                 'газобетонный завод Xella, кирпичные заводы '
                 'Wienerberger.',
    'g4734fbe4': 'Небоскрёб в комплексе «Москва-Сити» (411 тыс. кв. м); '
                 'в 2023 году 85% площади выкупило РЖД по обязательству '
                 'правительства.',
}

# Перенаправление ролей сделки: id -> {поле: новое значение}.
ROLE_FIXES = {
    'g52730430': {'buyer': NEW_BUYER_ID, 'target': NEW_TARGET_ID},
}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    comps = data['companies']
    deals_by_id = {d['id']: d for d in data['deals']}

    for new_id, new_c in ((NEW_BUYER_ID, NEW_BUYER), (NEW_TARGET_ID, NEW_TARGET)):
        assert new_id not in comps, 'id %s уже занят' % new_id
        for c in comps.values():
            assert c.get('name') != new_c['name'], 'имя %r уже занято' % new_c['name']
        print('  НОВЫЙ ПРОФИЛЬ %-12s %s' % (new_id, new_c['name']))

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
        print('  ОПИСАНИЕ %-12s %-34s %s' % (cid, str(c.get('name'))[:34], text[:50]))
        c['desc'] = text
        wrote += 1

    for cid, fields in ROLE_FIXES.items():
        d = deals_by_id.get(cid)
        assert d, 'сделки %s нет в базе' % cid
        assert d.get('buyer') is None, 'buyer сделки %s уже не пуст: %r' % (cid, d.get('buyer'))
        assert d.get('target') == 'gba35c8d8', ('target сделки %s уже другой: %r'
                                                  % (cid, d.get('target')))
        for field, new_val in fields.items():
            print('  РОЛЬ %s.%s -> %s' % (cid, field, new_val))
            d[field] = new_val

    if not write:
        real = sum(1 for v in comps.values()
                   if (v.get('desc') or '').strip() and not PLACEHOLDER.match(str(v.get('desc'))))
        real += 2  # два новых профиля, ещё не добавленных в comps в сухом прогоне
        total = len(comps) + 2
    else:
        comps[NEW_BUYER_ID] = NEW_BUYER
        comps[NEW_TARGET_ID] = NEW_TARGET
        real = sum(1 for v in comps.values()
                   if (v.get('desc') or '').strip() and not PLACEHOLDER.match(str(v.get('desc'))))
        total = len(comps)

    print('\nОписаний записано: %d (+2 новых профиля)' % wrote)
    print('Сделок с исправленными ролями: %d' % len(ROLE_FIXES))
    if skipped:
        print('Пропущено (уже есть своё описание): %d' % len(skipped))
        for cid, name, old in skipped[:5]:
            print('   %s %s — %r' % (cid, name, old))

    print('Всего профилей с описанием: %d из %d (%d%%)'
          % (real, total, round(100 * real / total)))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
