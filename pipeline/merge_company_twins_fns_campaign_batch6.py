#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Три профиля-близнеца, найденные волной 3 самопроверки ИНН вебом
(28 августа 2026, `pipeline/fns_registry.py`) — тот же класс, что уже
чинили `merge_company_twins_fns_campaign*.py`: одно и то же юрлицо на
двух разных карточках компании, не два профиля одной сделки.

  * «АИГ Страховая Компания» / «АО СК Гардия» — АИГ переименована в
    «Гардию» 27.12.2022 (ИНН 7710541631), две РАЗНЫЕ сделки на разных
    картах (продажа Russia Partners в 2022-м; ЛУКОЙЛ/Газпромбанк —
    Фрезия получили контроль позже).
  * Medical Visual Systems / ООО «Медицинские системы визуализации» —
    один и тот же разработчик (ИНН 7813214820, гендиректор Андрей
    Кобец), два РАЗНЫХ инвестраунда на разных карточках (Фонд НТИ вложил
    325 млн ₽; позже РФПИ и УК «Первая» вложили 1 млрд ₽).
  * «Сибан Холдинг» / «Сибантрацит» — покупатель Sibanthracite PLC у
    группы «Аллтек» переименован в «Сибантрацит Холдинг» (ИНН
    9703035596), две РАЗНЫЕ сделки (покупка у наследников Босова; позже
    Башкирский промышленный холдинг купил уже «Сибантрацит»).

ПРОВЕРЕНО ПЕРЕД СЛИЯНИЕМ: ни одна пара не описывает одну и ту же сделку
дважды, роли не пересекаются.

КАК ВЫБИРАЛСЯ ОСТАЮЩИЙСЯ ПРОФИЛЬ — тот же порядок: больше ролей — меньше
переписывать; при равенстве — тот, что уже несёт `confirmed` в реестре
ФНС (не терять готовую синхронизацию). У всех трёх пар — 1/1 ролей,
остаётся confirmed-профиль.

ЗАПИСИ РЕЕСТРА ФНС ПОСЛЕ СЛИЯНИЯ — снимаются ОТДЕЛЬНОЙ правкой того же
`pipeline/fns_registry.py` (не этим скриптом), как и в прошлые разы.

Запуск:
    python3 pipeline/merge_company_twins_fns_campaign_batch6.py            # сухой прогон
    python3 pipeline/merge_company_twins_fns_campaign_batch6.py --write    # записать
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'
REFS = ('buyer', 'seller_id', 'target', 'asset_id')

# (остаётся, удаляется, ожидаемые имена, почему так)
MERGE = [
    ('geebb5d31', 'g8d204e38', ('АО СК Гардия', 'АИГ Страховая Компания'),
     'ролей поровну (1/1); остаётся профиль с уже подтверждённым в реестре ФНС ИНН (текущее имя компании)'),
    ('g1183e341', 'gd8f276ab', ('ООО «Медицинские системы визуализации»', 'Medical Visual Systems'),
     'ролей поровну (1/1); остаётся профиль с уже подтверждённым в реестре ФНС ИНН'),
    ('g0278b9c4', 'g9ebfa06f', ('Сибантрацит', 'ООО «Сибан Холдинг»'),
     'ролей поровну (1/1); остаётся профиль с уже подтверждённым в реестре ФНС ИНН (текущее имя компании)'),
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

    print('СЛИЯНИЕ ПРОФИЛЕЙ-БЛИЗНЕЦОВ (волна 3 самопроверки ИНН): %d пар, переезжает %d ролей\n'
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
