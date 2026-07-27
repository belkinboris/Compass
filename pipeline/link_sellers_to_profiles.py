# -*- coding: utf-8 -*-
"""Связывание текстовых продавцов с профилями компаний (бэклог A4).

Продавец извлекается из текста как строка (`seller`), и только часть удалось
сразу сопоставить с профилем компании (`seller_id`). Из-за этого на странице
компании не показывалась сделка, где она продавала: связи-то нет.

Сопоставление строгое — только точное совпадение нормализованного названия с
названием профиля или с одним из его `match_keys`. Нечёткий поиск по подстроке
отвергнут: на прошлом таком сопоставлении он давал «Торговый дом ВКТ» ->
«Анна Фомичева» (это продавец, а не актив) и «персонализированных добавок» ->
«Персона» (совпадение внутри слова).

Дополнительно проверяем, что найденный профиль не занят в этой же сделке другой
ролью: компания не может быть одновременно продавцом и покупателем.

Запуск:
    python3 pipeline/link_sellers_to_profiles.py            # сухой прогон
    python3 pipeline/link_sellers_to_profiles.py --write    # записать
"""
import json
import re
import sys

PATH = 'static/data/deals_promoted.json'


def norm(s):
    s = (s or '').lower()
    s = re.sub(r'[«»"\'`]', '', s)
    s = re.sub(r'\b(?:ооо|оао|зао|пао|ао|гк|ук|нк|тоо|ltd|llc|inc|plc|group|групп|холдинг)\b', ' ', s)
    s = re.sub(r'[^\w\s]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    comps = data['companies']
    mk = data.get('match_keys') or {}

    # обратный индекс «нормализованное имя -> id профиля»
    rev = {}
    for cid, keys in mk.items():
        for k in (keys if isinstance(keys, list) else [keys]):
            n = norm(k)
            if len(n) >= 4:
                rev.setdefault(n, cid)
    for cid, c in comps.items():
        n = norm(c.get('name') or '')
        if len(n) >= 4:
            rev.setdefault(n, cid)

    linked = []
    for d in data['deals']:
        if not d.get('seller') or d.get('seller_id'):
            continue
        cid = rev.get(norm(d['seller']))
        if not cid:
            continue
        # профиль уже занят другой ролью в этой же сделке
        if cid in (d.get('buyer'), d.get('target'), d.get('asset_id')):
            continue
        linked.append((d['id'], d['seller'], cid, comps.get(cid, {}).get('name', '')))
        if write:
            d['seller_id'] = cid

    print(f'продавцов связано с профилем: {len(linked)}')
    for i, s, cid, n in linked:
        print(f'  {i} | {s[:30]!r:32} -> {n[:38]} ({cid})')

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
        print('\nЗАПИСАНО в', PATH)


if __name__ == '__main__':
    main(write='--write' in sys.argv)
