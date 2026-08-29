# -*- coding: utf-8 -*-
"""Побочный, но обязательный шаг месячной очереди 29 августа 2026:
`pipeline/fix_korsakov_port_login_delo_and_progress.py` завёл новый профиль
«ООО «Логин Дело»» с `holding.id = 'delo'` — а профиль «Группа компаний
«Дело»» (`delo`) не нёс `group: true`. Тест
`test_holding_target_is_always_flagged_as_group` (test_data.py) требует,
чтобы ЛЮБОЙ профиль, на который ссылается чей-то `holding.id`, был помечен
`group: true` — иначе на его карточке рисуется список «В группу входит: N»
без бейджа «Группа компаний» рядом с названием (см. CLAUDE.md, запись про
23 августа 2026, «группа vs фонд/инвестор»).

«Дело» — действительно группа компаний (в собственном названии профиля),
поэтому это не гадание, а перенос уже написанного в структурированное
поле, которого раньше не требовалось, пока у профиля не было ни одного
холдингового участника.

Запуск: python3 pipeline/fix_delo_group_flag.py
        python3 pipeline/fix_delo_group_flag.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

COMPANY_ID = 'delo'


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    company = data['companies'][COMPANY_ID]

    assert 'group' not in company, 'group уже стоит'
    assert company['name'] == 'Группа компаний «Дело»'

    print(f'=== {COMPANY_ID}: group -> True ===')

    if write:
        company['group'] = True
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
