# -*- coding: utf-8 -*-
"""Месячная очередь, 9 сентября 2026 — дочитывание карточки `g9f6fe860`
(«Selectel приобрёл облачного провайдера "Единая сеть" (Servers.ru)»,
добавлена в базу 3 августа 2026, полностью обыскана в тот же день).

Дельта-поиск (саб-агент + личная проверка) нашёл два новых факта. Личный
WebFetch (mergers.ru) подтвердил дословно:

1) Продавцы. «Владельцами компании являлись Людмила Губарева (66,13%),
   Татьяна Чистякова (20,95%) и Александр Двас (12,91%)» — карточка не
   называла продавца вовсе.

2) Финансовый консультант. «Консультантом сделки выступил бывший глава
   REG.RU Роман Муразанов» — добавлен в `law.adv` рядом с уже известным
   юридическим консультантом White Square.

Саб-агент также искал подтверждение выплаты earn-out (прогнозный платёж
1,1 млрд ₽ из `law.terms`) и точные показатели выручки за 2024 год — ни
то, ни другое прямо не подтверждено ни одним источником (только
косвенный, не первичный пересказ отчётности), поэтому НЕ вносится.

Запуск:
    python3 pipeline/fix_selectel_edinaya_set_seller_and_advisor.py            # сухой прогон
    python3 pipeline/fix_selectel_edinaya_set_seller_and_advisor.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

OLD_SELLER = None
NEW_SELLER = 'Людмила Губарева, Татьяна Чистякова и Александр Двас'

OLD_LAW_ADV = [
    [
        "Юридический консультант покупателя (Selectel)",
        "White Square",
        "Партнёр Елизавета Ракова, советник Валерий Лавров, юрист Григор Восканян, помощник юриста Данил Бессонов. Источник: https://t.me/LawFirms/8286",
    ]
]
NEW_LAW_ADV = OLD_LAW_ADV + [
    [
        "Финансовый консультант",
        "Роман Муразанов",
        "Бывший глава REG.RU выступил консультантом сделки. Источник: https://mergers.ru/news/Selectel-kupila-oblachnogo-provajdera-Edinaya-set-84509",
    ]
]

NEW_SRC = ['Mergers.ru', 'https://mergers.ru/news/Selectel-kupila-oblachnogo-provajdera-Edinaya-set-84509']


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    d = by_id['g9f6fe860']

    assert d.get('seller') == OLD_SELLER, \
        'g9f6fe860 seller уже занят: %r' % (d.get('seller'),)
    assert d['law']['adv'] == OLD_LAW_ADV, \
        'g9f6fe860 law.adv уже другой: %r' % (d['law']['adv'],)
    urls = {s[1] for s in d['src']}
    assert NEW_SRC[1] not in urls, 'источник уже добавлен'

    print('g9f6fe860: seller None -> три физлица-продавца; law.adv '
          'дополнен финансовым консультантом (Роман Муразанов); добавлен '
          'источник mergers.ru')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    d['seller'] = NEW_SELLER
    d['law']['adv'] = NEW_LAW_ADV
    d['src'].append(NEW_SRC)

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
