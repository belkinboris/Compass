# -*- coding: utf-8 -*-
"""Ручная выверка ролей сторон у карточек 2026 года.

2026 — витринный год базы, и именно в нём поле target чаще всего заполнено
не приобретаемым активом, а покупателем или продавцом. После перехода карточки
на схему «продавец → предмет → покупатель» это стало видно буквально: покупатель
подписывался «предметом сделки», а продавец — вообще не показывался.

Автоматика тут опасна (слишком разные формулировки), поэтому таблица ниже
выверена вручную по заголовку и тексту каждой карточки. Для каждой сделки
указано, чем на самом деле является компания, лежащая в target:
    'buyer'  — это покупатель, переносим в buyer
    'seller' — это продавец, переносим в seller_id
и, где нужно, название предмета сделки (asset), взятое из заголовка.

Запуск:
    python3 pipeline/fix_2026_roles.py           # сухой прогон
    python3 pipeline/fix_2026_roles.py --write   # записать
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'

# id -> (роль компании из target, название предмета сделки или None, доля или None)
FIX = {
    # --- в target лежит ПОКУПАТЕЛЬ ---
    'g718e3d0e': ('buyer',  'Flowwow', None),
    'g5f25f452': ('buyer',  'студия звукового постпродакшена Flysound', None),
    'gb92f7119': ('buyer',  'CarPrice и цифровые активы Александра Галицкого', None),
    'g339dfcc8': ('buyer',  '«Алгоритм1»', None),
    'g7e81d8e7': ('buyer',  'SuperJob', '80%'),
    'g36bc7831': ('buyer',  '«Русский холод»', None),
    'g18fd392a': ('buyer',  'Karpov.courses', '50,1%'),
    'g4e692f4b': ('buyer',  '«Новая вагоноремонтная компания»', '70%'),
    'g4470332e': ('buyer',  'доля в ВТБ', '5,33%'),
    'g14fd5ba9': ('buyer',  'Just AI', '4,15%'),
    'gecce5162': ('buyer',  '«Архилогик»', '20%'),
    'g676504a3': ('buyer',  'платформа сервисной робототехники', None),
    'g5eb6ff22': ('buyer',  'ГК «Дело»', '51%'),

    # --- в target лежит ПРОДАВЕЦ ---
    'g1edb1b9d': ('seller', 'часть российских активов АО «ЮниКредит Банк»', None),
    'g304f9065': ('seller', 'российские активы Louis Dreyfus Company', None),
    'g96ef3005': ('seller', 'акции АО «Амбер Талвис»', '72,9%'),
    'g10f783e8': ('seller', 'Moscow Towers', None),
    'gcc677615': ('seller', 'здание Рижского вокзала', None),
    'g489b4309-2': ('seller', 'казначейский пакет акций X5', '9,7%'),
    'ge8f45161': ('seller', 'Федеральная грузовая компания (ФГК)', '49%'),
    'ga402c91b': ('seller', 'активы АО «СПИ-РВВК» и ООО «РВВК»', None),
}


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    comps = data['companies']
    D = {d['id']: d for d in data['deals']}

    def cname(cid):
        c = comps.get(cid)
        return (c.get('name') if isinstance(c, dict) else None) or cid or '—'

    applied = {'buyer': 0, 'seller': 0, 'asset': 0}
    problems = []
    for did, (role, asset, share) in FIX.items():
        d = D.get(did)
        if not d:
            problems.append(f'{did}: нет такой сделки')
            continue
        tgt = d.get('target')
        if not tgt:
            problems.append(f'{did}: target уже пуст, пропуск')
            continue
        print(f'{did} | target «{cname(tgt)[:34]}» -> {role}')
        if write:
            if role == 'buyer':
                if not d.get('buyer'):
                    d['buyer'] = tgt
                    applied['buyer'] += 1
                d['target'] = None
                d['target_was_buyer'] = True
            else:
                if not d.get('seller_id'):
                    d['seller_id'] = tgt
                    d['seller'] = cname(tgt)
                    d['seller_src'] = 'manual_2026'
                    applied['seller'] += 1
                d['target'] = None
                d['target_was_seller'] = True
            if asset:
                d['asset'] = asset
                applied['asset'] += 1
                if share:
                    d['asset_share'] = share
                else:
                    d.pop('asset_share', None)

    print(f'\nвсего в таблице: {len(FIX)}')
    if problems:
        print('ПРОБЛЕМЫ:')
        for p in problems:
            print('  ', p)
    if write:
        print(f'проставлено buyer: {applied["buyer"]}, seller: {applied["seller"]}, asset: {applied["asset"]}')
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
        print('ЗАПИСАНО в', PATH)


if __name__ == '__main__':
    main(write='--write' in sys.argv)
