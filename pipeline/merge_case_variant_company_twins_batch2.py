# -*- coding: utf-8 -*-
"""Три профиля-близнеца, разрезанных падежом — вторая волна после
«Окуловской бумажной фабрики».

ЧТО СЛОМАНО. `test_no_company_twins` нормализует транслитерацию и
пунктуацию, но не русское склонение — прошлый прогон уже чинил один
такой случай точечно (`merge_okulovskaya_paper_factory_twin.py`).
На этот раз близнецов искали не глазами, а сплошным прогоном:
`pipeline/ingest/casing.py` умеет приводить голову словосочетания к
именительному падежу (написан для предмета сделки в заголовке, но
работает и на именах компаний) — прогон по всем 1871 профилю нашёл
ТРИ пары, где один профиль после приведения к именительному совпадает
с другим:

* «Европейский медицинский центр» (`gc536440f`, именительный, уже с
  описанием) / «Европейского медицинского центра» (`ge3150849`,
  родительный) — ОБА профиля со своей сделкой (IPO 2021 года у
  родительного, покупка «Семейного доктора» в 2025-м у именительного):
  это не гадательная пара, а один и тот же известный медицинский
  холдинг, разрезанный падежом на две карточки.
* «Богдановичский комбикормовый завод» (`g30346432`, именительный, без
  единой сделки) / «Богдановичского комбикормового завода» (`gbbe5bd50`,
  родительный, сделка Сибагро) — тот же рисунок, что «Окуловская бумажная
  фабрика»: профиль вырезан из заголовка сделки без приведения к
  начальной форме.
* «Ленинградский мельничный комбинат им. Кирова» (`gb30dfa0a`,
  именительный, уже с описанием «Куплен Сабуровским комбинатом
  хлебопродуктов») / «Ленинградского мельничного комбината им. Кирова»
  (`g145ff8ae`, родительный, сделка о покупке 100% акций тем самым
  Сабуровским комбинатом) — описание выжившего профиля само рассказывает
  об этой сделке, только `target` сделки указывал на падежный дубль, а
  не на профиль, где это уже написано.

Во всех трёх случаях выживает ИМЕНИТЕЛЬНЫЙ падеж (то имя, что видит
читатель на карточке компании), а не тот, что случайно попал первым в
базу; там, где у выжившего уже есть описание и отрасль — они не
трогаются, у Богдановичского завода описания не было — добавлено по
тексту его собственной сделки (выручка, объём производства, год
основания — Коммерсантъ, 6579487).

Каждая пара проверена перед записью: у профиля-дубля ровно ОДНА
ссылающаяся сделка в базе (`git grep`/полнотекстовый поиск id по всему
JSON, не только по `target`/`buyer`/`seller_id`/`asset_id`), и это та же
сделка, что assert проверяет по `id`.

Запуск:
    python3 pipeline/merge_case_variant_company_twins_batch2.py            # сухой прогон
    python3 pipeline/merge_case_variant_company_twins_batch2.py --write    # записать
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

# (dup_id, survivor_id, deal_id, ожидаемое имя дубля, ожидаемое имя выжившего)
PAIRS = [
    ('ge3150849', 'gc536440f', 'ga311fd12',
     'Европейского медицинского центра', 'Европейский медицинский центр'),
    ('gbbe5bd50', 'g30346432', 'gb43c8bcb',
     'Богдановичского комбикормового завода', 'Богдановичский комбикормовый завод'),
    ('g145ff8ae', 'gb30dfa0a', 'ga9be07b2',
     'Ленинградского мельничного комбината им. Кирова',
     'Ленинградский мельничный комбинат им. Кирова'),
]

NEW_DESC = {
    'g30346432': ('Российский производитель комбикормов в Свердловской '
                   'области, работает с 1988 года.'),
}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    companies = data['companies']
    deals = data['deals']

    for dup_id, survivor_id, deal_id, dup_name, survivor_name in PAIRS:
        assert companies[dup_id]['name'] == dup_name, 'дубль %s уже не тот' % dup_id
        assert companies[survivor_id]['name'] == survivor_name, 'выживший %s уже не тот' % survivor_id

        referencing = [d['id'] for d in deals
                       if d.get('target') == dup_id or d.get('buyer') == dup_id
                       or d.get('seller_id') == dup_id or d.get('asset_id') == dup_id]
        assert referencing == [deal_id], ('на дубль %s ссылается не одна сделка: %r'
                                           % (dup_id, referencing))

        full_text_refs = [d['id'] for d in deals if dup_id in json.dumps(d, ensure_ascii=False)]
        assert full_text_refs == [deal_id], ('дубль %s встречается не только в target/buyer: %r'
                                              % (dup_id, full_text_refs))

        print('СЛИВАЕМ  %s -> %s (%s)' % (dup_id, survivor_id, survivor_name))
        print('ПЕРЕНАПРАВЛЯЕМ  target/buyer сделки %s' % deal_id)

        if not write:
            continue

        for d in deals:
            if d.get('id') == deal_id:
                if d.get('target') == dup_id:
                    d['target'] = survivor_id
                if d.get('buyer') == dup_id:
                    d['buyer'] = survivor_id

        survivor_aliases = set(data['match_keys'].get(survivor_id, []))
        survivor_aliases.update(data['match_keys'].pop(dup_id, []))
        data['match_keys'][survivor_id] = sorted(survivor_aliases)

        data.setdefault('merged_companies', {})[dup_id] = survivor_id
        del companies[dup_id]

        if survivor_id in NEW_DESC:
            companies[survivor_id]['desc'] = NEW_DESC[survivor_id]
            print('ОПИСАНИЕ  %s: %s' % (survivor_id, NEW_DESC[survivor_id]))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0

    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
