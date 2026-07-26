# -*- coding: utf-8 -*-
"""Разбор профилей-компаний, в имя которых затесалась РОЛЬ в сделке.

Прошлый пайплайн иногда сохранял в названии компании не название, а подпись
стороны: «Осина Екатерина Борисовна (продавец 80% долей)», «АО «Новый старт» —
покупатель», «Teleperformance SE (первоначальный владелец, вышла из актива...)».
Это плохо дважды:
  1. Название компании отображается с канцелярским хвостом на всех страницах.
  2. Роль пропадает как данные — хотя это ровно то, чего не хватает карточке:
     кто продавец.

Скрипт делает две вещи:
  * вытаскивает роль и, если профиль помечен продавцом, проставляет сделке
    seller_id (и очищает target/buyer, если там стоял именно продавец);
  * чистит само название компании от ролевого хвоста.

Роль определяется по хвосту в скобках или после тире — то есть по служебной
приписке, а не по названию: «Группа «Продавец» не пострадает, потому что
проверяется именно вынесенная в конец пометка.

Запуск:
    python3 pipeline/clean_party_roles.py            # сухой прогон
    python3 pipeline/clean_party_roles.py --write    # записать
"""
import json
import re
import sys
import collections

PATH = 'static/data/deals_promoted.json'

# Служебный хвост: «... (продавец, 10%)», «... — покупатель», «... (продаваемая компания)»
TAIL_PAREN = re.compile(r'\s*\(([^()]*(?:продав|покупател|продаваем|приобретаем|'
                        r'первоначальн\w+\s+владел|вышла?\s+из\s+актива|остал\w+\s+с)[^()]*)\)\s*$', re.I)
TAIL_DASH = re.compile(r'\s*[—–-]\s*((?:продавец|покупатель|продаваемая\s+компания|'
                       r'приобретаемая\s+компания)[^,;]*)$', re.I)

# ВАЖНО: «продаваемая компания» — это сам актив, а не продавец, поэтому
# отсекаем её раньше, чем проверяем на «продав...».
ASSET_RX = re.compile(r'продаваем\w*\s+компани|приобретаем\w*\s+компани|продаваем\w*\s+актив', re.I)
SELLER_RX = re.compile(r'продавец|продавц\w+|первоначальн\w+\s+владел|вышла?\s+из\s+актива', re.I)
BUYER_RX = re.compile(r'покупател', re.I)


def split_role(name):
    """-> (чистое имя, текст роли) либо (имя, None)."""
    for rx in (TAIL_PAREN, TAIL_DASH):
        m = rx.search(name or '')
        if m:
            clean = (name[:m.start()]).strip(' ,;:—–-')
            if len(clean) >= 3:
                return clean, m.group(1).strip()
    return name, None


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    comps = data['companies']
    stats = collections.Counter()

    roles = {}          # cid -> 'seller' | 'buyer'
    renames = []
    for cid, c in comps.items():
        if not isinstance(c, dict):
            continue
        name = c.get('name') or ''
        clean, role = split_role(name)
        if not role:
            continue
        if ASSET_RX.search(role):
            roles[cid] = 'asset'
        elif SELLER_RX.search(role):
            roles[cid] = 'seller'
        elif BUYER_RX.search(role):
            roles[cid] = 'buyer'
        if clean != name:
            renames.append((cid, name, clean, role))

    print(f'профилей с ролевой припиской: {len(renames)}')
    print(f'  помечены продавцом: {sum(1 for v in roles.values() if v=="seller")}')
    print(f'  помечены покупателем: {sum(1 for v in roles.values() if v=="buyer")}')
    print(f'  помечены как сам актив: {sum(1 for v in roles.values() if v=="asset")}')
    print('\nпримеры переименования:')
    for cid, old, new, role in renames[:10]:
        print(f'  {cid}: {old[:56]!r}\n      -> {new[:56]!r}   [роль: {role[:34]}]')

    # проставляем продавца сделкам, где в target/buyer стоит профиль-«продавец»
    for d in data['deals']:
        for field in ('target', 'buyer'):
            cid = d.get(field)
            if not cid or roles.get(cid) != 'seller':
                continue
            # покупатель, помеченный продавцом, — противоречие, не трогаем
            if field == 'buyer' and not d.get('target'):
                continue
            if not d.get('seller_id') and not d.get('seller'):
                nm = comps.get(cid, {}).get('name') or ''
                d['seller_id'] = cid
                d['seller'] = split_role(nm)[0]
                d['seller_src'] = 'profile_role'
                stats['seller_from_profile'] += 1
            if field == 'target' and d.get('seller_id') == cid and d.get('buyer'):
                d['target'] = None
                d['target_was_seller'] = True
                stats['target_cleared'] += 1

    if write:
        for cid, old, new, role in renames:
            comps[cid]['name'] = new
            # роль сохраняем как данные: она нужна дальше по пайплайну, чтобы
            # не подписать продавца «предметом сделки» (см. fix_target_roles.py)
            if roles.get(cid):
                comps[cid]['role_hint'] = roles[cid]
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
        print('\nЗАПИСАНО в', PATH)

    print(f"\nпродавец проставлен из роли профиля: {stats['seller_from_profile']}")
    print(f"target очищен (там был продавец): {stats['target_cleared']}")


if __name__ == '__main__':
    main(write='--write' in sys.argv)
