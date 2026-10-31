# -*- coding: utf-8 -*-
"""«Окуловская бумажная фабрика» — два профиля одной компании.

ЧТО СЛОМАНО. `g30bcda98` — «Окуловская бумажная фабрика» (именительный
падеж, без единой сделки в базе). `gb6ffbafa` — «Окуловской бумажной
фабрики» (родительный падеж, вырезан из фразы «приобрела 100% долей
Окуловской бумажной фабрики» без приведения к начальной форме) — именно
на него ссылается сделка `gc215d8b0` («Каппа РУС» приобрела 100% долей).
Это одна и та же компания, разрезанная падежом на два профиля:
`test_no_company_twins` такое не ловит — его ключ транслитерирует и
убирает пунктуацию, но не приводит русское склонение к одной форме, а
«окуловская...» и «окуловской...» после этого остаются разными строками.
Тот же класс дефекта, что уже чинили у «Башнефти»/«Башнефть»
(`merge_bashneft_twin_and_clean_aliases.py`) — падежная форма имени,
попавшая в профиль вместо начальной.

Заодно у ОБОИХ профилей была неверна отрасль: `g30bcda98` — «Химия и
удобрения», `gb6ffbafa` — «Пищепром и напитки». Ни то ни другое не
описывает бумажную фабрику; собственная сделка называет предмет прямо —
«Окуловская бумажная фабрика», производство бумаги. Верная категория —
«Лесопром» (тот же выбор, что уже сделан для Metsä Group в батче 11: лес
и целлюлозно-бумажная переработка, не химия и не пищепром).

ЧТО ДЕЛАЕТ. Сливает `gb6ffbafa` в `g30bcda98` (выживает именительный
падеж — это то имя, которое видит читатель на карточке компании),
перенаправляет `target` сделки `gc215d8b0`, переносит алиас в
`match_keys` (чтобы будущий приток по родительному падежу тоже находил
этот профиль, а не создавал третьего близнеца), ставит отрасль
«Лесопром» и однострочное описание.

Запуск:
    python3 pipeline/merge_okulovskaya_paper_factory_twin.py            # сухой прогон
    python3 pipeline/merge_okulovskaya_paper_factory_twin.py --write    # записать
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

DUP_ID = 'gb6ffbafa'
SURVIVOR_ID = 'g30bcda98'
DEAL_ID = 'gc215d8b0'
NEW_IND = 'Лесопром'
NEW_DESC = 'Российская фабрика по производству бумаги, входит в группу «Каппа РУС».'


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    companies = data['companies']

    assert companies[DUP_ID]['name'] == 'Окуловской бумажной фабрики', 'дубль уже не тот'
    assert companies[SURVIVOR_ID]['name'] == 'Окуловская бумажная фабрика', 'профиль-выживший уже не тот'
    assert companies[DUP_ID]['ind'] == 'Пищепром и напитки', 'отрасль дубля уже другая'
    assert companies[SURVIVOR_ID]['ind'] == 'Химия и удобрения', 'отрасль выжившего уже другая'

    referencing = [d['id'] for d in data['deals']
                   if d.get('target') == DUP_ID or d.get('buyer') == DUP_ID
                   or d.get('seller_id') == DUP_ID or d.get('asset_id') == DUP_ID]
    assert referencing == [DEAL_ID], 'на дубль ссылается не одна сделка: %r' % referencing

    print('СЛИВАЕМ  %s -> %s (Окуловская бумажная фабрика)' % (DUP_ID, SURVIVOR_ID))
    print('ПЕРЕНАПРАВЛЯЕМ  target сделки %s' % DEAL_ID)
    print('ОТРАСЛЬ  %s: Химия и удобрения -> %s' % (SURVIVOR_ID, NEW_IND))
    print('ОПИСАНИЕ  %s: %s' % (SURVIVOR_ID, NEW_DESC))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0

    for d in data['deals']:
        if d.get('id') == DEAL_ID and d.get('target') == DUP_ID:
            d['target'] = SURVIVOR_ID

    survivor_aliases = set(data['match_keys'].get(SURVIVOR_ID, []))
    survivor_aliases.update(data['match_keys'].pop(DUP_ID, []))
    data['match_keys'][SURVIVOR_ID] = sorted(survivor_aliases)

    data.setdefault('merged_companies', {})[DUP_ID] = SURVIVOR_ID
    del companies[DUP_ID]

    companies[SURVIVOR_ID]['ind'] = NEW_IND
    companies[SURVIVOR_ID]['desc'] = NEW_DESC

    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
