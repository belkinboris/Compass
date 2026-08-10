# -*- coding: utf-8 -*-
"""Профиль `target` карточки g6663f201 («ГК «Урбантех» приобрела 30% ООО
«Нетвижн»») назван «ЗПИФ «Инфинит», ЗПИФ «Борей», ЗПИФ «Интеграл», Казаченко
Роман Юрьевич» — имя, не встречающееся НИ В ОДНОМ источнике карточки. Разбор
дал сбой: слово «инфинит» пришло не из статьи о сделке, а из фрагмента
рекламного JS-скрипта на странице-источнике («вызывается следующий баннер в
инфинит скролле», infinite scroll) — совпадение по подстроке при сборе
профиля приняло код за имя стороны.

Сама карточка (`eco.share`, `eco.context`, `law.struct`) верно и подробно
описывает предмет сделки как ООО «Нетвижн» — эта строка и идёт в имя
профиля. Единственная ссылающаяся сделка — g6663f201 (проверено прогоном
без записи), риск задеть чужие карточки нулевой.

Запуск: python3 pipeline/fix_netvizhn_profile_wrong_name.py           # проверка
        python3 pipeline/fix_netvizhn_profile_wrong_name.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

COMPANY_ID = 'g006e1e6c'
OLD_NAME = 'ЗПИФ «Инфинит», ЗПИФ «Борей», ЗПИФ «Интеграл», Казаченко Роман Юрьевич'
NEW_NAME = 'ООО «Нетвижн»'
OLD_ALIASES = ['зпиф инфинит, зпиф борей, зпиф интеграл, казаченко роман юрьевич',
               'инфинит', 'борей', 'интеграл']
NEW_ALIASES = ['ооо нетвижн', 'нетвижн']


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    company = data['companies'].get(COMPANY_ID)
    assert company is not None, 'профиля %s больше нет' % COMPANY_ID
    assert company['name'] == OLD_NAME, 'имя уже другое: %r' % company['name']
    assert data['match_keys'].get(COMPANY_ID) == OLD_ALIASES, 'псевдонимы уже другие'
    refs = [d['id'] for d in data['deals']
            if d.get('target') == COMPANY_ID or d.get('buyer') == COMPANY_ID
            or d.get('seller') == COMPANY_ID]
    assert refs == ['g6663f201'], 'на профиль ссылается не одна сделка: %r' % refs

    print('ПРАВИМ  %s: %r -> %r' % (COMPANY_ID, OLD_NAME, NEW_NAME))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    company['name'] = NEW_NAME
    data['match_keys'][COMPANY_ID] = NEW_ALIASES
    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
