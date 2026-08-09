# -*- coding: utf-8 -*-
"""Правка предыдущего скрипта (`fix_profile_names_genitive_instrumental.py`)
создала близнеца, а не почин: переименование `g05adc740` «Башнефти» ->
«Башнефть» столкнулось с уже существующим верным профилем `gf9a640d2`
«Башнефть» — `test_no_company_twins` поймал это сразу же. Правильный ход тот
же, что уже описан в CLAUDE.md для профилей-близнецов (прогон 51): не
переименовывать испорченный профиль, а слить его со верным и перенаправить
единственную ссылающуюся сделку (gf6232eec, `target`) на профиль-выживший.

Заодно чистит второй хвост того же прогона: `match_keys['g83d157e5']` («ООО
„Центр фармацевтической упаковки"») нёс те же протёкшие фрагменты роли
(«объект приобретения»), что чинили в имени профиля, — их тоже роняет
`test_match_key_alias_is_a_name`.

Запуск: python3 pipeline/merge_bashneft_twin_and_clean_aliases.py
        python3 pipeline/merge_bashneft_twin_and_clean_aliases.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

DUP_ID = 'g05adc740'
SURVIVOR_ID = 'gf9a640d2'
PACKAGING_ID = 'g83d157e5'
BAD_ALIASES = {
    'ооо центр фармацевтической упаковки (объект приобретения)',
    'объект приобретения',
}


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    companies = data['companies']
    assert companies[DUP_ID]['name'] == 'Башнефть', 'дубль уже не тот'
    assert companies[SURVIVOR_ID]['name'] == 'Башнефть', 'профиль-выживший уже не тот'

    redirected = [d['id'] for d in data['deals']
                  if d.get('target') == DUP_ID or d.get('buyer') == DUP_ID
                  or d.get('seller') == DUP_ID]
    assert redirected == ['gf6232eec'], 'на дубль ссылается не одна сделка: %r' % redirected

    old_aliases = set(data['match_keys'].get(PACKAGING_ID, []))
    assert old_aliases & BAD_ALIASES, 'протёкших псевдонимов уже нет'

    print('СЛИВАЕМ  %s -> %s (Башнефть); перенаправляем target у gf6232eec' % (DUP_ID, SURVIVOR_ID))
    print('ЧИСТИМ   match_keys[%s]: убираем %r' % (PACKAGING_ID, sorted(old_aliases & BAD_ALIASES)))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    for d in data['deals']:
        if d.get('id') == 'gf6232eec' and d.get('target') == DUP_ID:
            d['target'] = SURVIVOR_ID

    survivor_aliases = set(data['match_keys'].get(SURVIVOR_ID, []))
    survivor_aliases.update(data['match_keys'].pop(DUP_ID, []))
    data['match_keys'][SURVIVOR_ID] = sorted(survivor_aliases)

    data.setdefault('merged_companies', {})[DUP_ID] = SURVIVOR_ID
    del companies[DUP_ID]

    data['match_keys'][PACKAGING_ID] = sorted(old_aliases - BAD_ALIASES)

    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
