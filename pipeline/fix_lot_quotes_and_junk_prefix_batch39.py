# -*- coding: utf-8 -*-
"""Тридцать девятая партия: 8 описаний + два дефекта имени профиля.

ДЕФЕКТ 1. `gec2fae6c` носил имя «Экзософт» , «Номари СиАйЭс» , «Ресолют
БЕЗ первой открывающей и последней закрывающей кавычки (плюс лишний
пробел перед каждой запятой) — тот же класс, что чинили в партиях 36 и
38 («Букет Чувашии»/«Булгарпиво», «ПК-ТЕРМОСНАБ»/«ТЕРМОКЛИП»). Три
ИТ-компании, купленные ГК «Астра» одной сделкой (текст источника прямо
их перечисляет), признака `lot` тоже не было. Имя починено, пробелы
убраны, `lot: true` проставлен.

ДЕФЕКТ 2. `gef7aace4` носил имя «Иск Sian Participation» — слово «Иск»
(«судебный иск») перед именем компании, явно попавшее из заголовка
сделки («Иск Sian Participation... к Domidias...»), а не часть
названия офшорной структуры Магомедова. Переименовано в «Sian
Participation» (id и текущее имя проверены — коллизий с другими
профилями нет).

ЧТО ДЕЛАЕТ. 8 описаний + 2 починки имени (одна с признаком `lot`).

Запуск:
    python3 pipeline/fix_lot_quotes_and_junk_prefix_batch39.py            # сухой прогон
    python3 pipeline/fix_lot_quotes_and_junk_prefix_batch39.py --write    # записать
"""
import json
import re
import sys

DATA = 'static/data/deals_promoted.json'
PLACEHOLDER = re.compile(r'^\s*(описание компании пока не добавлено'
                          r'|профиль сформирован по итогам чтения)', re.I)

LOT_ID = 'gec2fae6c'
LOT_OLD_NAME = 'Экзософт» , «Номари СиАйЭс» , «Ресолют'
LOT_NEW_NAME = '«Экзософт», «Номари СиАйЭс», «Ресолют»'

PREFIX_ID = 'gef7aace4'
PREFIX_OLD_NAME = 'Иск Sian Participation'
PREFIX_NEW_NAME = 'Sian Participation'

DESCRIPTIONS = {
    LOT_ID: 'Три ИТ-компании, купленные ГК «Астра» одной сделкой в '
            '2024 году: разработчики ISPSystem, Knomary и GitFlic.',
    PREFIX_ID: 'Офшорная структура Зиявудина Магомедова; судится в '
               'Лондоне со структурой Марка Гарбера за исполнение '
               'опциона на пакет акций FESCO.',
    'geca16a9c': 'Три актива сети ветклиник Vet Union (Инвитро) — '
                 'операционная компания и два смежных бизнеса; в 2024 '
                 'году проданы Дмитрию Кокину.',
    'gedcf4bdc': 'Продуктовый стартап; в 2023 году фонд «Тилтех '
                 'Капитал» купил 20% акций в рамках seed-раунда.',
    'ged2d56b7': 'Агрохолдинг; в 2025 году купил 85% долей '
                 'производителя салатов «Прованс».',
    'gec7d014c': 'Предприниматель; купил у Кирилла Бохана '
                 'процессинговую компанию E1 Card.',
    'gec77bc9b': 'Производитель электроинструментов «Интерскол»; в '
                 '2024 году УК «Первая» вложила 1 млрд рублей.',
    'gebf162ee': 'Цементный завод в Краснодарском крае; в 2022 году '
                 'продан на торгах компании «Бизнес-Инвест» за 4,39 '
                 'млрд рублей.',
}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    comps = data['companies']

    lot = comps[LOT_ID]
    assert lot['name'] == LOT_OLD_NAME, 'имя %s уже другое: %r' % (LOT_ID, lot['name'])
    assert not lot.get('lot'), 'признак lot у %s уже стоит' % LOT_ID
    print('  ИМЯ ЛОТА %s: %r -> %r' % (LOT_ID, LOT_OLD_NAME, LOT_NEW_NAME))
    print('  ПРИЗНАК lot -> True (%s)' % LOT_ID)
    if write:
        lot['name'] = LOT_NEW_NAME
        lot['lot'] = True

    pfx = comps[PREFIX_ID]
    assert pfx['name'] == PREFIX_OLD_NAME, 'имя %s уже другое: %r' % (PREFIX_ID, pfx['name'])
    for c in comps.values():
        assert c.get('name') != PREFIX_NEW_NAME, 'имя %r уже занято' % PREFIX_NEW_NAME
    print('  ИМЯ %s: %r -> %r' % (PREFIX_ID, PREFIX_OLD_NAME, PREFIX_NEW_NAME))
    if write:
        pfx['name'] = PREFIX_NEW_NAME

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
        print('  ОПИСАНИЕ %-12s %s' % (cid, text[:50]))
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
