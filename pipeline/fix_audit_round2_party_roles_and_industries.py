# -*- coding: utf-8 -*-
"""Побочные находки чтения 17 пар-кандидатов в дубли (аудит, раунд 2,
6 сентября 2026): стороны не в своей роли и отрасль не той сущности.

ЧТО ЧИНИТ.

1. Покупатель — конкретное юрлицо, а не группа (правило владельца от
   18 августа: «заголовок называет бренд, buyer — конкретное юрлицо»):
   - `domodedovo-aukcion`: buyer `sheremetyevo` → `g127cf704` (ООО
     «Перспектива», дочка «Шереметьево», holding уже стоит). Профиль
     «Перспективы» после слияния дубля gf13fba9e остался бы без единой
     сделки, хотя именно она заключила договор с ПСБ;
   - `g12370211` («Альфа-банк покупает блокирующий пакет в «Кассир.ру»»):
     buyer `ga2cfae5b` («Альфа-Банк») → `g67e6a0e1` (ОАО «АБ Холдинг» —
     головная структура банка, реальный покупатель по РБК/Ъ, у профиля уже
     есть ЕГРЮЛ-доля и ещё одна сделка). Страница «Альфа-Банка» находит
     сделку по имени в заголовке.
2. Связь дочки с группой: ООО «Айриэлтор» (`g7f169e77`, прямой покупатель
   SmartDeal) получает `holding` → «Циан» (`g163cfc8b`) — после слияния
   дубля g4ac0a0a7 (где покупателем стоял бренд) страница «Циана» видит
   сделку через «В группу входит».
3. Предметом сделки стоит сам инвестор: у трёх карточек фонда «ТилТех»
   `target = g90031892` — это профиль самого фонда, а предмет (DocMed,
   SONNO, Shine Is) не назван ни профилем, ни текстом. Класс «предметом
   стоит покупатель» (CLAUDE.md), находится только чтением. Фонд переезжает
   в `buyer` (профиль «ТилТех» у трёх других сделок уже стоит покупателем;
   у 3Stream — отдельного фонда группы — своего профиля нет, он остаётся
   текстом), предмет — текстом из заголовка в именительном падеже.
4. Отрасль — про сделку, а не про сторону:
   - профиль `ge0bac578` (ПАО «B2B-РТС», оператор электронных торговых
     площадок): «Рынок ценных бумаг» → «ИТ и интернет» — вслед за
     карточкой IPO, которую переводит слияние;
   - `gd3ba954d` (ВЭБ.РФ купил 25% «Просвещения» у Сбера): «Медиа» →
     «Образование», как у профиля «Просвещения» и соседней карточки второй
     покупки (gf9932079).

Каждая правка — под assert на исходное состояние; если данные уже другие,
скрипт падает, а не перезаписывает. Уже применённая правка узнаётся и
пропускается — повторный прогон безопасен.

Запуск:
    python3 pipeline/fix_audit_round2_party_roles_and_industries.py           # сухой прогон
    python3 pipeline/fix_audit_round2_party_roles_and_industries.py --write
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

BUYER_REPOINT = {
    # id сделки: (старый buyer, новый buyer, имя нового профиля)
    'domodedovo-aukcion': ('sheremetyevo', 'g127cf704', 'ООО «Перспектива»'),
    'g12370211': ('ga2cfae5b', 'g67e6a0e1', 'ОАО «АБ Холдинг»'),
}

HOLDING = {
    'g7f169e77': {'id': 'g163cfc8b', 'confidence': 'disclosed',
                  'source': ['Интерфакс', 'https://www.interfax.ru/amp/898723']},
}

FUND = 'g90031892'  # профиль «ТилТех»
TILTECH = {
    # id: (buyer, buyer_name, asset, бренд предмета — обязан стоять в заголовке)
    'g47844a63': (FUND, None, 'сеть клиник доказательной медицины DocMed (ООО «Докдети Холдинг»)', 'DocMed'),
    'ga7a0b957': (FUND, None, 'косметический бренд Shine Is', 'Shine Is'),
    'g4a8bd86d': (None, 'Фонд 3Stream (группа «ТилТех»)', 'бренд товаров для сна SONNO', 'SONNO'),
}

DEAL_IND = {'gd3ba954d': ('Медиа', 'Образование')}
COMPANY_IND = {'ge0bac578': ('Рынок ценных бумаг', 'ИТ и интернет')}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    deals = {d['id']: d for d in data['deals']}
    comps = data['companies']

    for did, (old, new, name) in BUYER_REPOINT.items():
        d = deals[did]
        if d.get('buyer') == new:
            print(f'{did}: buyer уже {new}'); continue
        assert d.get('buyer') == old, (did, d.get('buyer'))
        assert comps[new]['name'] == name, comps[new]['name']
        assert new not in (d.get('target'), d.get('seller_id'), d.get('asset_id')), 'профиль уже в другой роли'
        print(f'{did}: buyer {old} -> {new} ({name})')
        if write:
            d['buyer'] = new

    for cid, holding in HOLDING.items():
        c, group = comps[cid], comps[holding['id']]
        assert c.get('holding') in (None, holding), (cid, c.get('holding'))
        assert group['name'] == 'Циан'
        print(f'{cid} ({c["name"]}): holding -> {holding["id"]} ({group["name"]}); у группы group: true')
        if write:
            c['holding'] = holding
            # цель holding обязана нести group: true — иначе на её странице есть список
            # «В группу входит», а бейджа «Группа компаний» нет (test_holding_target_is_always_flagged_as_group)
            group['group'] = True

    assert comps[FUND]['name'] == 'ТилТех'
    for did, (buyer, buyer_name, asset, brand) in TILTECH.items():
        d = deals[did]
        if d.get('target') is None and d.get('asset') == asset:
            print(f'{did}: предмет уже {asset!r}'); continue
        assert d.get('target') == FUND, (did, d.get('target'))
        assert not d.get('asset') and not d.get('buyer'), (did, d.get('asset'), d.get('buyer'))
        assert brand in d['title'] and brand in asset, (did, brand)
        assert 'Докдети' not in asset or 'Докдети' in json.dumps(d, ensure_ascii=False), did
        print(f'{did}: target {FUND} -> None; buyer={buyer} buyer_name={buyer_name!r}; asset={asset!r}')
        if write:
            d['target'] = None
            d['buyer'] = buyer
            d['buyer_name'] = buyer_name
            d['asset'] = asset

    for did, (old, new) in DEAL_IND.items():
        if deals[did].get('ind') == new:
            print(f'{did}: ind уже {new!r}'); continue
        assert deals[did].get('ind') == old, (did, deals[did].get('ind'))
        print(f'{did}: ind {old!r} -> {new!r}')
        if write:
            deals[did]['ind'] = new
    for cid, (old, new) in COMPANY_IND.items():
        if comps[cid].get('ind') == new:
            print(f'{cid}: ind уже {new!r}'); continue
        assert comps[cid].get('ind') == old, (cid, comps[cid].get('ind'))
        print(f'{cid} ({comps[cid]["name"]}): ind {old!r} -> {new!r}')
        if write:
            comps[cid]['ind'] = new

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
