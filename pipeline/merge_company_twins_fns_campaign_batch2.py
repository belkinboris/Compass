# -*- coding: utf-8 -*-
"""Два профиля-близнеца, найденные партией П2-7 (стороны сделок 2025 года,
pipeline/fns_registry.py) — тот же класс дефекта и тот же способ находки,
что уже чинил pipeline/merge_company_twins_fns_campaign.py (партия
22-23 августа для 2026 года): кампания сопоставления с ФНС подтверждала
ИНН по точному имени профиля, и поиск дважды вернул ИНН, уже занятый ДРУГИМ
профилем той же реальной компании под другим именем.

ЧТО СЛИТО (2 пары):
  * «ООО «Группа Русская энергия»» / «Русская энергия» — одна и та же
    компания-продавец бизнес-центра Art Plaza, под полным юрлицом и под
    кратким брендовым именем на двух разных карточках.
  * «Норильский никель» / «Норникель» — одна и та же компания (ПАО «ГМК
    «Норильский никель»), под полным и под кратким разговорным именем.

КАК ВЫБИРАЛСЯ ОСТАЮЩИЙСЯ ПРОФИЛЬ — тот же порядок, что в merge_company_
twins.py и в первой партии кампании: (1) больше ролей в сделках — меньше
ссылок переписывать; (2) при равенстве — профиль с уже подтверждённым ИНН
в pipeline/fns_registry.py остаётся. Здесь оба критерия совпадают в пользу
одного и того же профиля в обеих парах: «Группа Русская энергия» (2 роли
против 1, ИНН 7714456916, подтверждён 22 августа) и «Норильский никель»
(2 роли против 1, ИНН 8401005730, подтверждён 23 августа) — конкуренции
нет, выбор очевиден.

ЧТО ДЕЛАТЬ С РЕЕСТРОМ ФНС ПОСЛЕ СЛИЯНИЯ. Не задача этого скрипта —
удаляемые id («gee90a2b1», «g72e3b46f») просто не попадают в
pipeline/fns_registry.py отдельной записью (в партии П2-7 они изначально
были no_match с пометкой «профиль-близнец», ровно как в первой партии).

Запуск:
    python3 pipeline/merge_company_twins_fns_campaign_batch2.py            # сухой прогон
    python3 pipeline/merge_company_twins_fns_campaign_batch2.py --write    # записать
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'
REFS = ('buyer', 'seller_id', 'target', 'asset_id')

# (остаётся, удаляется, ожидаемые имена, почему так)
MERGE = [
    ('g5d22aa06', 'gee90a2b1', ('ООО «Группа Русская энергия»', 'Русская энергия'),
     'у «Группы Русская энергия» 2 роли против 1, и она уже подтверждена в реестре ФНС '
     '(партия 22 августа, ИНН 7714456916)'),
    ('g2f93d858', 'g72e3b46f', ('Норильский никель', 'Норникель'),
     'у «Норильского никеля» 2 роли против 1, и он уже подтверждён в реестре ФНС '
     '(партия 23 августа, ИНН 8401005730)'),
]


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    comps, deals, keys = data['companies'], data['deals'], data['match_keys']

    for keep, drop, names, _why in MERGE:
        assert keep in comps and drop in comps, 'профиля нет: %s / %s' % (keep, drop)
        assert (comps[keep]['name'], comps[drop]['name']) == names, \
            'имена изменились: %r против %r' % ((comps[keep]['name'], comps[drop]['name']), names)
        both = [d['id'] for d in deals
                if {d.get(f) for f in REFS} >= {keep, drop}]
        assert not both, 'сделка ссылается на оба профиля сразу: %s' % both

    moved = 0
    plan = []
    for keep, drop, names, why in MERGE:
        n = sum(1 for d in deals for f in REFS if d.get(f) == drop)
        aliases = [a for a in (keys.get(drop) or []) if a not in (keys.get(keep) or [])]
        plan.append((keep, drop, names, why, n, aliases))
        moved += n

    print('СЛИЯНИЕ ПРОФИЛЕЙ-БЛИЗНЕЦОВ (кампания ФНС, партия 2): %d пар, переезжает %d ролей\n' % (len(MERGE), moved))
    for keep, drop, names, why, n, aliases in plan:
        print('  «%s» <- «%s»' % (names[0], names[1]))
        print('      %s -> %s | ролей переезжает: %d | псевдонимов добавится: %d %s'
              % (drop, keep, n, len(aliases), aliases or ''))
        print('      почему: %s' % why)

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return

    было = len(comps)
    for keep, drop, _names, _why, _n, aliases in plan:
        for d in deals:
            for f in REFS:
                if d.get(f) == drop:
                    d[f] = keep
        if aliases:
            keys[keep] = (keys.get(keep) or []) + aliases
        keys.pop(drop, None)
        comps.pop(drop)
        data.setdefault('merged_companies', {})[drop] = keep

    assert len(comps) == было - len(MERGE), 'удалилось не столько профилей, сколько пар'
    for d in deals:
        refs = [d.get(f) for f in REFS if d.get(f)]
        assert len(refs) == len(set(refs)), 'после слияния компания заняла две роли: %s' % d['id']
    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('\nЗаписано. Профилей: %d (было %d). Переставлено ролей: %d.'
          % (len(comps), было, moved))


if __name__ == '__main__':
    main('--write' in sys.argv)
