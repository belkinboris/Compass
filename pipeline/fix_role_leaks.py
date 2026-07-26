# -*- coding: utf-8 -*-
"""Точечные правки ролей и названий, найденные при выверке 2022-2025 (бэклог A3).

Четыре разных дефекта, каждый выверен вручную по заголовку сделки:

1. УТЕЧКА РОЛИ ИЗ ПРОФИЛЯ. У профиля компании роль общая для всех сделок, а роль
   в сделке — своя. «ПАО «Газпром» … — продавец» сделал Газпрома продавцом и в
   той сделке, где он ПОКУПАЕТ Aurus. Сам источник утечки закрыт в
   clean_party_roles.py; здесь чиним уже записанные данные.

2. ОБРЕЗАННЫЕ НАЗВАНИЯ КОМПАНИЙ. В профиль попало одно слово из фразы:
   «Государственный» вместо «Государственный пенсионный фонд Норвегии»,
   «Федеральной» вместо «Федеральная грузовая компания».

3. МОЯ ЖЕ ОШИБКА ИЗ ВЫВЕРКИ 2026. В сделке «РЖД планирует продать 49% ФГК» я
   пометил продавцом саму ФГК — хотя ФГК это предмет сделки, а продаёт РЖД.

4. ВЫКУП СОБСТВЕННЫХ АКЦИЙ без единой стороны: у карточки ТМК не заполнено
   ничего, хотя покупатель назван прямо в заголовке.

Запуск:
    python3 pipeline/fix_role_leaks.py            # сухой прогон
    python3 pipeline/fix_role_leaks.py --write    # записать
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'

# id компании -> корректное название (взято из заголовка сделки, где она фигурирует)
RENAME = {
    'g0aded109': 'Государственный пенсионный фонд Норвегии (GPFG / NBIM)',
    'gc904414e': 'Федеральная грузовая компания (ФГК)',
    'gbb0eae3f': 'Новомет',
}


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    comps = data['companies']
    D = {d['id']: d for d in data['deals']}
    log = []

    # 1. Название компании обрезано до одного слова
    for cid, good in RENAME.items():
        cur = comps.get(cid, {}).get('name')
        if cur is None:
            log.append(f'{cid}: профиля нет, пропуск')
            continue
        if cur == good:
            continue
        log.append(f'название {cid}: {cur!r} -> {good!r}')
        if write:
            comps[cid]['name'] = good

    # 2. Продавец, «протёкший» из профиля в слот покупателя
    d = D.get('g94dcc5cc')
    if d and d.get('seller_id') and d['seller_id'] == d.get('buyer'):
        log.append('g94dcc5cc: продавец совпадал с покупателем (Газпром покупает Aurus) — продавец снят')
        if write:
            for k in ('seller', 'seller_id', 'seller_src'):
                d.pop(k, None)

    # 3. «РЖД продаёт 49% ФГК»: продавец — РЖД, а ФГК это предмет сделки
    d = D.get('ge8f45161')
    if d and d.get('seller_id') == 'gc904414e':
        log.append('ge8f45161: продавцом значилась ФГК (предмет сделки) — продавец заменён на РЖД')
        if write:
            d['seller_id'] = 'g8ec7e7bf'          # профиль РЖД
            d['seller'] = 'РЖД'
            d['seller_src'] = 'manual_a3'
            d['asset'] = 'Федеральная грузовая компания (ФГК)'
            d['asset_id'] = 'gc904414e'
            d['asset_share'] = '49%'

    # 4. Пенсионный фонд Норвегии значился ПРЕДМЕТОМ сделки, хотя он продавец:
    #    «GPFG объявил о продаже всех российских активов» — продаёт он, а предмет
    #    сделки это сами активы.
    d = D.get('g3074f98b')
    if d and d.get('target') == 'g0aded109':
        log.append('g3074f98b: фонд GPFG значился предметом сделки — перенесён в продавцы')
        if write:
            d['seller_id'] = 'g0aded109'
            d['seller'] = 'Государственный пенсионный фонд Норвегии (GPFG / NBIM)'
            d['seller_src'] = 'manual_a3'
            d['target'] = None
            d['target_was_seller'] = True
            d['asset'] = 'все российские активы фонда'

    # 5. Выкуп собственных акций: покупатель назван в заголовке, но поля пусты
    d = D.get('geb18dcad')
    if d and not d.get('buyer') and not d.get('target'):
        log.append('geb18dcad: выкуп собственных акций ТМК — проставлен покупатель и предмет')
        if write:
            d['buyer'] = 'ge00b1b13'              # профиль ТМК
            d['asset'] = 'собственные акции ТМК'
            d['asset_share'] = '0,1829%'

    for line in log:
        print(' ', line)
    print(f'\nвсего правок: {len(log)}')
    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
        print('ЗАПИСАНО в', PATH)


if __name__ == '__main__':
    main(write='--write' in sys.argv)
