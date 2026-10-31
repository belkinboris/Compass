"""Ренессанс Капитал / Онэксим (g995f83cf): в карточке не было ни покупателя,
ни продавца, хотя источники называют обоих (владелец, 12 октября 2026:
«там нет ни покупателя, ни продавца… лютый проеб»).

Интерфакс, 13.11.2024: «Группа „Онэксим“ продала российский бизнес… менеджменту
инвесткомпании во главе с Максимом Орловским, Владимиром Куровым и Игорем
Даниленко». Коммерсантъ (doc/7298596) — то же, с указанием, что „Онэксим“
принадлежит Михаилу Прохорову. Дата карточки — первая новость (13 ноября), а не
пост юрфирмы Orion (22 ноября). Без --write — сухой прогон."""
import json, sys
DATA = 'static/data/deals_promoted.json'
ID = 'g995f83cf'
NEW = dict(buyer_name='Максим Орловский, Владимир Куров и Игорь Даниленко (топ-менеджеры)',
           seller='ООО «Группа Онэксим»', seller_src='text', date='2024-11-13')

def apply(data):
    x = next(x for x in data['deals'] if x['id'] == ID)
    assert x.get('buyer') is None and not x.get('buyer_name') and not x.get('seller'), x
    assert x['date'] == '2024-11-22', x['date']
    for k, v in NEW.items():
        print(f'{k}: {x.get(k)!r} -> {v!r}')
        x[k] = v

apply(json.load(open(DATA, encoding='utf-8')))
if '--write' in sys.argv:
    data = json.load(open(DATA, encoding='utf-8'))   # перечитать перед записью
    apply(data)
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('записано')
