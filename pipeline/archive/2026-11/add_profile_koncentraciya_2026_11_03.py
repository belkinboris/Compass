# -*- coding: utf-8 -*-
"""Профиль цели карточки g2ab91f78: АО «Концентрация» (ранее AppScience),
химический холдинг. ИНН не найден живым поиском (WebSearch, rusprofile
заблокирован) — отдельная сверка ФНС (docs/company_data.md), сюда не
ставится.
Запуск: python3 add_profile_koncentraciya_2026_11_03.py --write (из каталога pipeline/archive/2026-11)
"""
import json
import os
import sys
from datetime import datetime, timezone

ROOT = '/home/user/Compass'
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')


def new_id(existing):
    n = 0
    while True:
        candidate = 'g%08x' % ((abs(hash(str(datetime.now(timezone.utc)) + str(n)))) % (16 ** 8))
        if candidate not in existing:
            return candidate
        n += 1


def main():
    write = '--write' in sys.argv[1:]
    data = json.load(open(DATA, encoding='utf-8'))
    pending = json.load(open(PENDING, encoding='utf-8'))
    companies = data['companies']

    target_id = new_id(companies)
    companies[target_id] = {
        'name': 'АО «Концентрация»',
        'legal_name': 'АО «Концентрация»',
        'ind': 'Химия и удобрения',
        'desc': ('Российский химический холдинг (ранее — AppScience), развивает локализацию '
                 'малотоннажной «сложной химии» для фармацевтики, косметики и нефтехимии на '
                 'контрактных и собственных производственных площадках.'),
    }

    found = False
    for c in pending['cards']:
        if c['id'] == 'g2ab91f78':
            found = True
            assert c.get('asset') == 'АО «Концентрация»', c.get('asset')
            c['target'] = target_id
    if not found:
        raise SystemExit('g2ab91f78 не найдена в pending.json')

    print('target_id=%s' % target_id)
    if write:
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('ЗАПИСАНО')
    else:
        print('Сухой прогон. Запись — с ключом --write.')


if __name__ == '__main__':
    main()
