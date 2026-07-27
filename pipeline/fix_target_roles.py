# -*- coding: utf-8 -*-
"""Починка поля target там, где в нём лежит не приобретаемый актив, а другая роль.

Поле target по замыслу — приобретаемый актив. Но генератор карточек местами
клал туда покупателя или продавца, и карточка сделки показывала это буквально:
«Сыктывкарский ЛПК приобрел ПармаВуд» рендерилось как предмет сделки =
«Сыктывкарский ЛПК», то есть покупатель был подписан как то, что купили.

Две правки:
  1. target = ПОКУПАТЕЛЬ. Признак: buyer пуст, а заголовок начинается с названия
     компании из target, за которым идёт глагол приобретения. Тогда переносим
     target -> buyer.
  2. target = ПРОДАВЕЦ, но продавец у сделки уже определён из другого источника.
     Тогда target точно не актив — очищаем, чтобы не подписывать продавца
     «предметом сделки».

Запуск:
    python3 pipeline/fix_target_roles.py            # сухой прогон
    python3 pipeline/fix_target_roles.py --write    # записать
"""
import json
import re
import sys

PATH = 'static/data/deals_promoted.json'

VERB = re.compile(
    r'(?:приобрел|приобрёл|приобрела|купил|купила|выкупил|выкупила|покупает|'
    r'приобретает|консолидировал\w*|инвестировал\w*|получил|получила)', re.I)

# Предмет сделки из заголовка: всё после глагола приобретения и до продавца
# («у X»), суммы («за N») или конца. Нужен там, где у актива нет своей карточки
# компании — иначе в структуре сделки середина остаётся пустой.
ASSET_RX = re.compile(
    r'(?:приобрел[аои]?|приобрёл|приобрета(?:ет|ют)|купил[аои]?|покупает|выкупил[аои]?|'
    r'консолидировал[аи]?|получил[аи]?|инвестировал[аи]?\s+в|вложил[аи]?\s+в)'
    r'\s+(.{3,80}?)(?=$|,|;|\s+у\s+[А-ЯA-Z]|\s+за\s+[\d~«]|\s+—|\s+\(|\s+в\s+рамках)', re.I)


def norm(s):
    s = (s or '').lower()
    s = re.sub(r'[«»"\'`]', '', s)
    s = re.sub(r'\b(?:ооо|оао|зао|пао|ао|гк|ук|группа|групп|холдинг)\b', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    comps = data['companies']

    def cname(cid):
        c = comps.get(cid)
        return (c.get('name') if isinstance(c, dict) else None) or ''

    moved, cleared = [], []
    for d in data['deals']:
        tgt = d.get('target')
        if not tgt:
            continue
        name = cname(tgt)
        title = d.get('title') or ''

        # 1) target на самом деле покупатель
        if not d.get('buyer') and name:
            nn = norm(name)
            if len(nn) >= 4:
                head = norm(title[:len(name) + 16])
                if head.startswith(nn[:max(6, len(nn) // 2)]) and VERB.search(title[:130]):
                    moved.append((d['id'], name, title[:70]))
                    if write:
                        d['buyer'] = tgt
                        d['target'] = None
                        d['target_was_buyer'] = True
                    continue

        # 2) target — продавец, а продавец уже известен из другого источника
        if d.get('seller') and d.get('seller_id') != tgt:
            tc = comps.get(tgt) or {}
            role_marked = tc.get('role_hint') == 'seller' or re.search(r'продав', name, re.I)
            if role_marked:
                cleared.append((d['id'], name, title[:70]))
                if write:
                    d['target'] = None
                    d['target_was_seller'] = True

    # третий проход: у сделок без карточки актива достаём его название из заголовка
    #
    # Долю («80% долей…») выносим отдельным полем — она информативна сама по себе.
    # Для самого названия берём имя в кавычках, если оно есть; иначе оставляем фразу
    # целиком. Соблазн «угадать» имя по последним словам с заглавной мы отвергли:
    # на реальных заголовках это давало «Нижнем Новгороде» вместо «Александрия»
    # и «Double» вместо «One & Double».
    SHARE_RX = re.compile(
        r'^(\d{1,3}(?:[.,]\d+)?\s*%)\s*(?:долей|доли|доля|акций|акции|'
        r'уставного\s+капитала)?\s*(?:в\s+)?', re.I)
    QUOTED_RX = re.compile(r'«([^»]{2,50})»')
    assets = 0
    for d in data['deals']:
        if d.get('target') or not d.get('buyer'):
            d.pop('asset', None)
            continue
        d.pop('asset_share', None)
        m = ASSET_RX.search(d.get('title') or '')
        if m:
            a = m.group(1).strip(' ,;:.—–-')
            share = ''
            sm = SHARE_RX.match(a)
            if sm:
                share = sm.group(1).replace(' ', '')
                a = a[sm.end():].strip()
            quoted = QUOTED_RX.findall(a)
            if quoted:
                a = ' и '.join(quoted)
            else:
                a = a.strip(' ,;:.—–-«»')
                if a.count('«') > a.count('»'):
                    a += '»'
                a = re.sub(r'\s+(?:на|в|у|за|из|от|по|для)$', '', a)
            # осмысленное название: не короче 3 символов и содержит буквы
            if 3 <= len(a) <= 80 and re.search(r'[А-Яа-яA-Za-z]{3}', a):
                assets += 1
                if write:
                    d['asset'] = a
                    if share:
                        d['asset_share'] = share
                continue
        d.pop('asset', None)

    print(f'предмет сделки извлечён из заголовка: {assets}')
    print(f'target -> buyer (в target лежал покупатель): {len(moved)}')
    for i, n, t in moved:
        print(f'  {i} | {n[:34]!r}  <- {t}')
    print(f'\ntarget очищен (там был продавец, продавец уже известен): {len(cleared)}')
    for i, n, t in cleared:
        print(f'  {i} | {n[:34]!r}  <- {t}')

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
        print('\nЗАПИСАНО в', PATH)


if __name__ == '__main__':
    main(write='--write' in sys.argv)
