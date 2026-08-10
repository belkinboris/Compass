# -*- coding: utf-8 -*-
"""Падежные близнецы среди самых известных компаний базы — третья волна
после «Окуловской бумажной фабрики» и партии 2. Плюс один случай, который
оказался НЕ близнецом, а бэкапом.

ЧТО СЛОМАНО. Прошлые две находки ловились инструментом
`pipeline/ingest/casing.py` (приводит голову словосочетания к
именительному падежу). У него намеренно консервативные защиты — не
трогает слово, которое pymorphy распознаёт как имя/бренд/организацию
(`_looks_like_a_name`). Это защищает от порчи брендов вроде «Рив Гош»,
но и СКРЫВАЕТ близнецов там, где голова словосочетания — само название
компании: «Газпрома», «Мираторгом», «Ингосстраха» — однословные
названия, которые pymorphy помечает как Orgn/Name, и инструмент их не
трогает вовсе. Прогон по всей базе (0 пар) не значит «близнецов больше
нет» — значит «инструмент, заточенный под предмет сделки в заголовке, не
видит близнецов у однословных названий компаний». Нашлись прямым поиском
по стеблю известных брендов (Газпром, Мираторг, Лукойл, Ингосстрах)
среди профилей без описания.

* «Мираторг» (`gb8b82d2b`, именительный, с описанием) / «Мираторгом»
  (`g1b866bae`, творительный) — один из крупнейших производителей мяса
  в России, разрезан падежом на два профиля. НАСТОЯЩИЙ близнец, слит.
* «Ингосстрах» (`g4a281a8e`, именительный, с описанием) / «Ингосстраха»
  (`g67117389`, родительный) — крупная страховая компания, тот же
  рисунок. НАСТОЯЩИЙ близнец, слит.
* «ПАО «Газпром»» (`gc0f11fd7`, именительный, с описанием, 3 сделки) /
  «Газпрома» (`gfc48a6b2`, родительный, 1 сделка) / «Газпромом»
  (`g980c34ab`, творительный, 2 сделки) — ТРИ профиля одной компании
  одновременно. НАСТОЯЩИЕ близнецы, слиты.

«ЛУКОЙЛ» (`g5c8c6494`) / «Лукойла» (`g5d3d7e14`) — ПОХОЖ на близнеца
(тот же падежный рисунок), но слить его напрямую нельзя: сделка
`gfa1163ce` («Леонид Федун продал 10% акций Лукойла компании») несёт
`buyer=g5c8c6494` («компании», то есть сам ЛУКОЙЛ выкупает) и
`target=g5d3d7e14` — это обратный выкуп акций, и `target` здесь ссылается
не на компанию-эмитента отдельно от покупателя, а на САМ ПАКЕТ АКЦИЙ,
исторически записанный profile-заглушкой. Слияние `target` в тот же id,
что и `buyer`, ломает `test_one_company_holds_one_role_in_a_deal`
(компания не может быть в сделке одновременно и покупателем, и
предметом) — и ломает по делу: сделка правда говорит «X купил у Y пакет
акций X», а не «X купил X». Ровно так уже устроена другая сделка о
собственном выкупе в базе — Ivideon/`g25db4ede` (`buyer=Ivideon`,
`target=`отдельный профиль «собственная доля, выкупленная у
«Индустриального фонда»»). У «Лукойла» тот же случай, только вместо
пакета акций туда по ошибке попал падежный вариант имени самой компании.
Правка: `g5d3d7e14` НЕ сливается с `g5c8c6494` — переименовывается в
пакет акций по тому же образцу, что у Ivideon, и остаётся отдельным
профилем, на который по-прежнему указывает `target`.

Перед записью для каждого дубля/переименования проверено: id встречается
в JSON только в тех сделках, что перечислены здесь, — значит, профиль не
участвует ни в чём, кроме учтённого.

Запуск:
    python3 pipeline/merge_case_variant_company_twins_batch3.py            # сухой прогон
    python3 pipeline/merge_case_variant_company_twins_batch3.py --write    # записать
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

# (dup_id, survivor_id, [deal_ids], ожидаемое имя дубля, ожидаемое имя выжившего)
CLUSTERS = [
    ('g1b866bae', 'gb8b82d2b', ['gabc867f3'], 'Мираторгом', 'Мираторг'),
    ('g67117389', 'g4a281a8e', ['gf0b712ef'], 'Ингосстраха', 'Ингосстрах'),
    ('gfc48a6b2', 'gc0f11fd7', ['g85306500'], 'Газпрома', 'ПАО «Газпром»'),
    ('g980c34ab', 'gc0f11fd7', ['g4cd1fa52', 'g3bb1fadb'], 'Газпромом', 'ПАО «Газпром»'),
]

# Не близнец, а сделка обратного выкупа: этот профиль переименовывается
# в пакет акций (по образцу Ivideon/g25db4ede), а не сливается.
BUYBACK_STAKE_ID = 'g5d3d7e14'
BUYBACK_STAKE_OLD_NAME = 'Лукойла'
# Без «%» и «акций» — test_company_name_is_not_a_deal_composition (CLAUDE.md
# «Имя компании — не место для доли») запрещает и то и другое в имени
# профиля; тот же приём словами, что у Ivideon/g25db4ede («собственная
# доля, выкупленная у «Индустриального фонда»»).
BUYBACK_STAKE_NEW_NAME = 'Доля в ЛУКОЙЛе, выкупленная у Леонида Федуна'
BUYBACK_DEAL_ID = 'gfa1163ce'
BUYBACK_BUYER_ID = 'g5c8c6494'  # ЛУКОЙЛ — уже стоит в buyer, не трогаем


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    companies = data['companies']
    deals = data['deals']

    for dup_id, survivor_id, deal_ids, dup_name, survivor_name in CLUSTERS:
        assert companies[dup_id]['name'] == dup_name, 'дубль %s уже не тот' % dup_id
        assert companies[survivor_id]['name'] == survivor_name, 'выживший %s уже не тот' % survivor_id

        full_text_refs = sorted(d['id'] for d in deals if dup_id in json.dumps(d, ensure_ascii=False))
        assert full_text_refs == sorted(deal_ids), (
            'дубль %s встречается не только в учтённых сделках: %r' % (dup_id, full_text_refs))

        print('СЛИВАЕМ  %s -> %s (%s)' % (dup_id, survivor_id, survivor_name))
        print('ПЕРЕНАПРАВЛЯЕМ  сделки', deal_ids)

        if write:
            for d in deals:
                if d.get('id') in deal_ids:
                    if d.get('target') == dup_id:
                        d['target'] = survivor_id
                    if d.get('buyer') == dup_id:
                        d['buyer'] = survivor_id
                    if d.get('seller_id') == dup_id:
                        d['seller_id'] = survivor_id
                    if d.get('asset_id') == dup_id:
                        d['asset_id'] = survivor_id

            survivor_aliases = set(data['match_keys'].get(survivor_id, []))
            survivor_aliases.update(data['match_keys'].pop(dup_id, []))
            data['match_keys'][survivor_id] = sorted(survivor_aliases)

            data.setdefault('merged_companies', {})[dup_id] = survivor_id
            del companies[dup_id]

    # Обратный выкуп: не сливаем, переименовываем в пакет акций.
    assert companies[BUYBACK_STAKE_ID]['name'] == BUYBACK_STAKE_OLD_NAME, 'профиль пакета уже не тот'
    d = next(d for d in deals if d['id'] == BUYBACK_DEAL_ID)
    assert d['buyer'] == BUYBACK_BUYER_ID, 'buyer сделки обратного выкупа уже не тот'
    assert d['target'] == BUYBACK_STAKE_ID, 'target сделки обратного выкупа уже не тот'
    full_text_refs = sorted(dd['id'] for dd in deals if BUYBACK_STAKE_ID in json.dumps(dd, ensure_ascii=False))
    assert full_text_refs == [BUYBACK_DEAL_ID], (
        'профиль пакета встречается не только в сделке обратного выкупа: %r' % full_text_refs)

    print('ПЕРЕИМЕНОВЫВАЕМ  %s: %r -> %r (обратный выкуп, не близнец)'
          % (BUYBACK_STAKE_ID, BUYBACK_STAKE_OLD_NAME, BUYBACK_STAKE_NEW_NAME))
    if write:
        companies[BUYBACK_STAKE_ID]['name'] = BUYBACK_STAKE_NEW_NAME
        data['match_keys'][BUYBACK_STAKE_ID] = [BUYBACK_STAKE_NEW_NAME.lower()]

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0

    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
