# -*- coding: utf-8 -*-
"""Четыре профиля-близнеца, найденные кампанией сопоставления с ФНС
(22-23 августа 2026, pipeline/fns_registry.py) — тот же класс дефекта,
что уже чинил pipeline/merge_company_twins.py (A22), но эти пары ключ той
кампании (транслитерация/пунктуация) не ловил: имена расходятся не
написанием одного и того же слова, а формой бренда/юрлица.

КАК НАШЛОСЬ. Кампания подтверждала ИНН по точному имени профиля — и на
каждой из четырёх карточек поиск то возвращал уже занятый другим профилем
ИНН, то (для «Mail»/«VK») тест `test_fns_registry_one_inn_is_not_confirmed_
to_two_profiles` прямо поймал бы задвоение. Оставлены в реестре как
`no_match` с пометкой «профиль-близнец» до этого слияния — сопоставлять с
ФНС нечего, пока не решено, какой из двух профилей главный.

ЧТО СЛИТО (4 пары):
  * «Лента» / «Группа Лента» — один и тот же ритейлер под двумя карточками
    (короткое старое имя и текущее «Группа Лента» после редомициляции).
  * «банк «Открытие»» / «ФК Открытие» — один банк, присоединённый к ВТБ в
    2022 году, описан на двух карточках почти одинаковым текстом.
  * «Аптечная сеть 36,6» / «Аптечная группа «36,6»» — одна аптечная сеть,
    описания дословно пересекаются («Российская аптечная сеть» и «Аптечная
    сеть федерального масштаба»).
  * «Mail» / «VK» — один интернет-холдинг до и после переименования 2021
    года (desc «Mail» сам это утверждает: «в 2021 году переименован в
    VK»).

КАК ВЫБИРАЛСЯ ОСТАЮЩИЙСЯ ПРОФИЛЬ — тот же порядок, что в merge_company_
twins.py: (1) больше ролей в сделках — меньше ссылок переписывать; (2) при
равенстве ролей — профиль с уже подтверждённым ИНН в pipeline/
fns_registry.py остаётся, чтобы не терять готовую синхронизацию с ФНС.
«Лента»: у «Группы Лента» 5 ролей против 4 — она и остаётся (плюс это уже
подтверждённый в реестре профиль, партия 3). «Открытие»: у «ФК Открытие»
4 роли против 3. «36,6»: ролей поровну (2/2), решает готовый ИНН —
остаётся «Аптечная группа «36,6»» (партия 4, ИНН 7722266450), а не
«Аптечная сеть 36,6». «Mail»/«VK»: у «VK» 13 ролей против 2 — не
конкуренция, а очевидный выбор (текущее имя бренда к тому же).

ЧТО ДЕЛАТЬ С ЗАПИСЯМИ РЕЕСТРА ФНС ПОСЛЕ СЛИЯНИЯ. Не задача этого скрипта —
`pipeline/fns_registry.py` правится отдельно (записи-заглушки для четырёх
удаляемых id снимаются, `SUSPECTED_TWIN_PROFILES` в
`pipeline/fns_unresolved_queue.py` больше не нужен).

Запуск:
    python3 pipeline/merge_company_twins_fns_campaign.py            # сухой прогон
    python3 pipeline/merge_company_twins_fns_campaign.py --write    # записать
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'
REFS = ('buyer', 'seller_id', 'target', 'asset_id')

# (остаётся, удаляется, ожидаемые имена, почему так)
MERGE = [
    ('gcca31da7', 'g10f70324', ('Группа Лента', 'Лента'),
     'у «Группы Лента» 5 ролей против 4, и она уже подтверждена в реестре ФНС (партия 3, ИНН 3906399157)'),
    ('g7ac0b3cc', 'g5941cd82', ('ФК Открытие', 'банк «Открытие»'),
     'у «ФК Открытие» 4 роли против 3'),
    ('g871b8a8a', 'gec1422a6', ('Аптечная группа «36,6»', 'Аптечная сеть 36,6'),
     'ролей поровну (2/2); остаётся профиль с уже подтверждённым ИНН (партия 4, 7722266450) — не терять готовую синхронизацию с ФНС'),
    ('g4e694234', 'g1d6e1cf7', ('VK', 'Mail'),
     'у «VK» 13 ролей против 2, и это действующее имя бренда — «Mail» сам утверждает в desc, что переименован в VK в 2021 году'),
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

    print('СЛИЯНИЕ ПРОФИЛЕЙ-БЛИЗНЕЦОВ (кампания ФНС): %d пар, переезжает %d ролей\n' % (len(MERGE), moved))
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
