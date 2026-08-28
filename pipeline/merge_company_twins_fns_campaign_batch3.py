# -*- coding: utf-8 -*-
"""Четыре профиля-близнеца, найденные партиями 2 и 3 самопроверки ИНН
вебом (28 августа 2026, `pipeline/fns_registry.py`) — тот же класс, что уже
чинили `merge_company_twins_fns_campaign.py`/`merge_company_twins_fns_
campaign_batch2.py`: живой поиск подтверждал ИНН, уже занятый ДРУГИМ
company_id того же реального юрлица.

ПРОВЕРЕНО ПЕРЕД СЛИЯНИЕМ (у каждой пары свои роли не пересекаются — в
отличие от «Инграда»/Sminex, здесь ни одна пара НЕ описывает одну и ту же
сделку дважды, только разные сделки одной компании):
  * «М.Видео» / «М.Видео-Эльдорадо» — один и тот же ритейлер электроники.
  * «Капитал Life» / «ООО «Капитал Лайф Страхование Жизни»» — одна и та
    же страховая компания.
  * «НПО КИС» / «НПО «Критические информационные системы»» — полное и
    сокращённое имя одного и того же предприятия Росатома.
  * «ВымпелКом» / «ПАО «Вымпел-Коммуникации»» — один и тот же оператор
    «Билайн».

КАК ВЫБИРАЛСЯ ОСТАЮЩИЙСЯ ПРОФИЛЬ — тот же порядок, что в прошлых слияниях
этого класса: больше ролей в сделках — меньше ссылок переписывать. У трёх
пар остающийся профиль однозначно сильнее (2 против 1, 2 против 1, 4
против 1); у «Капитал Life» роли равны (1/1) — решает то, что `gc9ade2d1`
уже нёс `confirmed` в реестре ДО этой кампании (партия по «Капитал Life»
была раньше, `g9dbb760c` лишь попытался подтвердить ТОТ ЖЕ ИНН заново и
получил дубль-предупреждение) — не терять готовую синхронизацию с ФНС.

ЗАПИСИ РЕЕСТРА ФНС ПОСЛЕ СЛИЯНИЯ. `test_fns_registry_company_ids_exist_
in_base` требует, чтобы каждый company_id реестра существовал в базе —
четыре `no_match`-заглушки удаляемых профилей (записаны партиями 2-3 при
попытке подтвердить уже занятый ИНН) сняты ОТДЕЛЬНОЙ правкой того же
`pipeline/fns_registry.py`, не этим скриптом (та же граница, что и в
предыдущих слияниях этого класса — правки данных и правки реестра решают
разные задачи).

Запуск:
    python3 pipeline/merge_company_twins_fns_campaign_batch3.py            # сухой прогон
    python3 pipeline/merge_company_twins_fns_campaign_batch3.py --write    # записать
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'
REFS = ('buyer', 'seller_id', 'target', 'asset_id')

# (остаётся, удаляется, ожидаемые имена, почему так)
MERGE = [
    ('g444cac01', 'g0608eb46', ('М.Видео', 'М.Видео-Эльдорадо'),
     'у «М.Видео» 2 роли против 1'),
    ('gc9ade2d1', 'g9dbb760c', ('Капитал Life', 'ООО «Капитал Лайф Страхование Жизни»'),
     'ролей поровну (1/1); остаётся профиль с уже подтверждённым в реестре ФНС ИНН'),
    ('gdccff9b3', 'g53fcd924', ('НПО КИС', 'НПО «Критические информационные системы»'),
     'у «НПО КИС» 2 роли против 1'),
    ('gd685b926', 'gd101d0a4', ('ВымпелКом', 'ПАО «Вымпел-Коммуникации»'),
     'у «ВымпелКом» 4 роли против 1'),
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

    print('СЛИЯНИЕ ПРОФИЛЕЙ-БЛИЗНЕЦОВ (партии 2-3 самопроверки ИНН): %d пар, переезжает %d ролей\n'
          % (len(MERGE), moved))
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
