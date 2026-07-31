#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Прямые кавычки вместо « » в названиях компаний и активов.

ЧТО СЛОМАНО. Проект последовательно использует «ёлочки» — тысячи «Меридиан»,
«Точка», «Эссити» по базе. У 12 карточек в `deals_promoted.json` название
осталось в прямых кавычках ("Марокское", "Точка", "Эссити" и т. д.) — похоже,
эти записи собирались из источника, где кавычки уже были прямыми, и их не
привели к общему виду. Разнобой заметен рядом: в одном предложении «Балтика»
и "Марокское".

ЧЕГО НЕ ТРОГАЕМ. Вложенные кавычки второго уровня — это не дефект, а
единственный способ написать имя внутри имени, когда «ёлочки» нельзя
вкладывать друг в друга: «Торговый дом "Меридиан"», «Группа "Астон"», «ГМК
"Дальполиметалл"» — все три уже в базе и в правильном формате. Правит скрипт
только СТАНДАЛОН прямые кавычки, где снаружи никаких «» нет вовсе.

ОСОБЫЙ СЛУЧАЙ g62cbdd8b. В перечислении трёх юрлиц у первых двух не хватало
закрывающих кавычек вовсе (открывающая «, а закрывающей » нет; открывающая "
без закрывающей): «СК "Орион плюс", вместо «СК "Орион плюс"»,. Это не смена
стиля, а починка оборванной пунктуации по тому же образцу вложенности,
что и у прошедших проверку карточек.

Правки идут по строковому замену с проверкой числа вхождений: если поле уже
не содержит старую подстроку (например, кто-то поправил её вручную), скрипт
падает, а не переписывает наугад.

Запуск:
    python3 pipeline/fix_straight_quotes.py            # сухой прогон
    python3 pipeline/fix_straight_quotes.py --write    # записать
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'

# id сделки -> список (поле, было, стало). Поле — 'extra' | 'title' | 'eco.rationale'
# (проверяется в обоих дублирующих полях, где текст совпадает дословно).
FIXES = {
    'g0a6cea12': [('extra', 'ООО "Марокское"', 'ООО «Марокское»'),
                  ('eco.rationale', 'ООО "Марокское"', 'ООО «Марокское»')],
    'ge56325d9': [('title', 'ТРЦ "Жемчужная плаза"', 'ТРЦ «Жемчужная плаза»')],
    'g88236336': [('extra', 'ООО "Банковские и финансовые системы"', 'ООО «Банковские и финансовые системы»'),
                  ('eco.rationale', 'ООО "Банковские и финансовые системы"', 'ООО «Банковские и финансовые системы»'),
                  ('extra', 'процессоров "Эльбрус"', 'процессоров «Эльбрус»'),
                  ('eco.rationale', 'процессоров "Эльбрус"', 'процессоров «Эльбрус»')],
    'g3b67afa3': [('extra', 'ПАО "М.Видео"', 'ПАО «М.Видео»'),
                  ('eco.rationale', 'ПАО "М.Видео"', 'ПАО «М.Видео»'),
                  ('extra', '"М.Видео - Эльдорадо"', '«М.Видео - Эльдорадо»'),
                  ('eco.rationale', '"М.Видео - Эльдорадо"', '«М.Видео - Эльдорадо»'),
                  ('extra', 'МКООО "Эрикария"', 'МКООО «Эрикария»'),
                  ('eco.rationale', 'МКООО "Эрикария"', 'МКООО «Эрикария»')],
    'g62cbdd8b': [('extra',
                    'ООО «СК "Орион плюс", ООО «Группа компаний "СМК-Инвест",',
                    'ООО «СК "Орион плюс"», ООО «Группа компаний "СМК-Инвест"»,'),
                  ('eco.rationale',
                    'ООО «СК "Орион плюс", ООО «Группа компаний "СМК-Инвест",',
                    'ООО «СК "Орион плюс"», ООО «Группа компаний "СМК-Инвест"»,')],
    'g4762fc3d': [('extra', '(ООО "ДИОН СОФТ")', '(ООО «ДИОН СОФТ»)'),
                  ('eco.rationale', '(ООО "ДИОН СОФТ")', '(ООО «ДИОН СОФТ»)')],
    'g46cc9712': [('extra', 'АО "Точка"', 'АО «Точка»'),
                  ('eco.rationale', 'АО "Точка"', 'АО «Точка»')],
    'g82c59e72': [('extra', 'ООО "Эссити"', 'ООО «Эссити»'),
                  ('eco.rationale', 'ООО "Эссити"', 'ООО «Эссити»')],
    'g75837e8b': [('extra', 'на счетах "С"', 'на счетах «С»'),
                  ('eco.rationale', 'на счетах "С"', 'на счетах «С»')],
}

# профили компаний: company_id -> (было, стало) в поле name
COMPANY_FIXES = {
    'gc9bafa49': ('ГК "Авторитэйл"', 'ГК «Авторитэйл»'),
}


def _get(deal, field):
    if '.' in field:
        block, sub = field.split('.', 1)
        return (deal.get(block) or {}).get(sub)
    return deal.get(field)


def _set(deal, field, value):
    if '.' in field:
        block, sub = field.split('.', 1)
        deal[block][sub] = value
    else:
        deal[field] = value


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    companies = data['companies']

    plan = []
    for deal_id, fixes in FIXES.items():
        deal = by_id.get(deal_id)
        assert deal is not None, 'нет сделки %s' % deal_id
        for field, old, new in fixes:
            current = _get(deal, field)
            assert current is not None and old in current, \
                '%s.%s: подстрока не найдена дословно: %r' % (deal_id, field, old[:60])
            assert current.count(old) == 1, '%s.%s: подстрока встречается не один раз' % (deal_id, field)
            plan.append((deal_id, field, old, new))

    company_plan = []
    for cid, (old, new) in COMPANY_FIXES.items():
        c = companies.get(cid)
        assert c is not None, 'нет компании %s' % cid
        assert c.get('name') == old, '%s: имя компании не совпадает дословно: %r' % (cid, c.get('name'))
        company_plan.append((cid, old, new))

    print('Карточек с прямыми кавычками вместо «»: %d (%d замен)' % (len(FIXES), len(plan)))
    for deal_id, field, old, new in plan:
        print('  %-12s %-16s %r -> %r' % (deal_id, field, old, new))
    print('Профилей компаний: %d' % len(company_plan))
    for cid, old, new in company_plan:
        print('  %-12s %r -> %r' % (cid, old, new))

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return

    for deal_id, field, old, new in plan:
        deal = by_id[deal_id]
        current = _get(deal, field)
        _set(deal, field, current.replace(old, new, 1))
    for cid, old, new in company_plan:
        companies[cid]['name'] = new

    for deal_id, field, old, new in plan:
        assert new in _get(by_id[deal_id], field), '%s.%s: новое значение не записалось' % (deal_id, field)
    for cid, old, new in company_plan:
        assert companies[cid]['name'] == new, '%s: имя не записалось' % cid

    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('\nЗаписано: %d замен в сделках, %d в профилях компаний.' % (len(plan), len(company_plan)))


if __name__ == '__main__':
    main('--write' in sys.argv)
