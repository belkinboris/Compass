# -*- coding: utf-8 -*-
"""Профили сторон карточки gf5bdb983: АО «Ремида» (продавец, группа «Носта»)
и ООО «Стройдевелопмент» (покупатель, группа «ССК»). ИНН — отдельной сверкой
ФНС (docs/company_data.md), сюда не ставится.
Запуск: python3 add_profiles_gf5bdb983.py --write (из каталога pipeline/archive/2026-11)
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

    seller_id = new_id(companies)
    companies[seller_id] = {
        'name': 'АО «Ремида»',
        'legal_name': 'АО «Ремида»',
        'ind': 'Строительство',
        'desc': ('Управляющая компания группы «Носта» — объединения ростовских и краснодарских '
                 'застройщиков, созданного московскими инвесторами; в 2022 году выкупила у ГК «ПИК» '
                 'права на последнюю очередь жилого комплекса «Норд» в Ростове-на-Дону.'),
    }

    buyer_id = new_id(companies)
    companies[buyer_id] = {
        'name': '«Стройдевелопмент»',
        'legal_name': 'ООО «Стройдевелопмент»',
        'ind': 'Строительство',
        'desc': 'Краснодарская девелоперская компания; входит в структуру застройщика «ССК» '
                '(Специализированный застройщик «СпецСтройКубань»).',
    }

    found = False
    for c in pending['cards']:
        if c['id'] == 'gf5bdb983':
            found = True
            assert c.get('seller') == 'АО «Ремида»', c.get('seller')
            assert c.get('buyer_name') == '«Стройдевелопмент»', c.get('buyer_name')
            c['seller_id'] = seller_id
            c['buyer'] = buyer_id
    if not found:
        raise SystemExit('gf5bdb983 не найдена в pending.json')

    print('seller_id=%s buyer_id=%s' % (seller_id, buyer_id))
    if write:
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('ЗАПИСАНО')
    else:
        print('Сухой прогон. Запись — с ключом --write.')


if __name__ == '__main__':
    main()
