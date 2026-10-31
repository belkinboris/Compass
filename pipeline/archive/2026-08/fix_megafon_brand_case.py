# -*- coding: utf-8 -*-
"""Профиль компании подписан «Мегафон», хотя бренд пишется «МегаФон».

В самой базе, в текстах карточек сделок, доминирует верное написание с
внутренней заглавной («МегаФон» — 21 упоминание против 6 «Мегафон»), а
профиль компании (та карточка, что показывается в каталоге, в поиске и в
плашке сторон) стоял в меньшинном, неверном варианте. Правим одно поле.

Запуск:
    python3 pipeline/fix_megafon_brand_case.py            # сухой прогон
    python3 pipeline/fix_megafon_brand_case.py --write    # записать
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'
CID = 'gf9d213b7'
OLD, NEW = 'Мегафон', 'МегаФон'


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    c = data['companies'][CID]
    actual = c.get('name')
    assert actual == OLD, f'{CID}.name: ожидали {OLD!r}, нашли {actual!r}'
    print(f'{CID} [company.name]: {OLD!r} -> {NEW!r}')
    if write:
        c['name'] = NEW
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
        print('\nЗАПИСАНО в', PATH)
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
