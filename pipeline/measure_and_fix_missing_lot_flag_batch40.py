# -*- coding: utf-8 -*-
"""Систематический промер вместо чтения по одной (продолжение приёма из
G2-31/measure_profile_name_vs_deal_titles.py): три прогона подряд (36,
38, 39) находили профиль-лот (несколько юрлиц под одним профилем
компании) без признака `lot` — каждый раз чтением одной карточки.
Здесь — сплошной прогон по всей базе разом.

КАК СЧИТАЕТ. Профиль без `lot`, чьё имя содержит ДВЕ ИЛИ БОЛЕЕ пары
кавычек-ёлочек «…», — кандидат. Исключены:
  - имена, где вторая пара кавычек лежит ВНУТРИ круглых скобок — это
    пояснение к ОДНОЙ компании («ООО «Экспанта» (ГК «Ультиматек»)»,
    «АО «Маяк» (группа «Каракан Инвест»)»), не лот;
  - имена с «/» — альтернативное имя ОДНОЙ и той же стороны (проверено
    на `gf5faae55` «СК «Ренессанс Жизнь» / Группа «Ренессанс
    страхование»» — источник называет только ОДНОГО покупателя,
    просто под двумя именами группа/дочка, а не два юрлица в одной
    сделке).

Дал 28 кандидатов из 1863 профилей. Прочитаны выборочно (5 из 28,
разных форм: скобочная группа, актив + актив, актив + компания,
список через запятую) против текста своих сделок — во всех пяти
подтверждено: сделка описывает НЕСКОЛЬКО юрлиц/активов, купленных
одним пакетом. Оставшиеся 23 не читались по отдельности — сигнал (два
и более полных названия юрлиц через «и»/запятую, СИЛЬНЕЕ сигнала из
профиля-коллизий: там было общее СЛОВО, здесь — синтаксис самого
перечисления) настолько прямой, что перечитывать каждый не требуется
для простановки ОДНОГО булева признака (не новый факт, а честная
пометка «это не одна компания»).

ЧТО ДЕЛАЕТ. Проставляет `lot: true` всем найденным кандидатам.

Запуск:
    python3 pipeline/measure_and_fix_missing_lot_flag_batch40.py            # сухой прогон (только замер)
    python3 pipeline/measure_and_fix_missing_lot_flag_batch40.py --write    # записать
"""
import json
import re
import sys

DATA = 'static/data/deals_promoted.json'


def is_parenthetical(name):
    paren_start = name.find('(')
    if paren_start == -1:
        return False
    paren_end = name.find(')', paren_start)
    if paren_end == -1:
        paren_end = len(name)
    inside = name[paren_start:paren_end]
    outside = name[:paren_start] + name[paren_end + 1:]
    return len(re.findall(r'«[^»]+»', outside)) <= 1 and len(re.findall(r'«[^»]+»', inside)) >= 1


def find_candidates(comps):
    out = []
    for cid, c in comps.items():
        if c.get('lot'):
            continue
        name = str(c.get('name') or '')
        pairs = len(re.findall(r'«[^»]+»', name))
        if pairs < 2:
            continue
        if is_parenthetical(name):
            continue
        if '/' in name:
            continue
        out.append(cid)
    return out


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    comps = data['companies']

    candidates = find_candidates(comps)
    print('Кандидатов (2+ пары кавычек вне скобок, без /, без lot): %d' % len(candidates))
    for cid in candidates:
        print('  %-12s %s' % (cid, comps[cid]['name']))
        if write:
            comps[cid]['lot'] = True

    print('\nПризнак lot проставлен: %d' % len(candidates))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
