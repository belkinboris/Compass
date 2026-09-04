# -*- coding: utf-8 -*-
"""Самопроверка этого же прогона (test_no_company_twins): карточка
`g7a3a83d1» и профиль `gkordiant2024» («ГК «Кордиант»»), построенные
этим прогоном для заметки 485, оказались ДУБЛЕМ уже существующей,
гораздо более полной карточки `g4a751f95» («Севергрупп купила активы
производителя шин Cordiant у S8 Capital») и профиля `gb52f53eb»
(«Cordiant») — их не нашли перед построением новой карточки (проверяли
только профили компаний по имени, а не заголовки существующих сделок).

`g4a751f95» несёт больше фактов (юридические консультанты, покупка
A.Raymond Group, точная дата перезапуска Gislaved, независимая оценка
22-29 млрд ₽) — она остаётся единственной. Дубль удаляется, `merged`
перенаправляет старый id на неё.

Запуск: python3 pipeline/fix_remove_duplicate_severgrupp_kordiant_card.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DUP_ID = 'g7a3a83d1'
SURVIVOR = 'g4a751f95'
DUP_COMPANY = 'gkordiant2024'


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)

    ids = {c['id'] for c in data['deals']}
    assert DUP_ID in ids
    assert SURVIVOR in ids
    assert DUP_COMPANY in data['companies']

    data['deals'] = [c for c in data['deals'] if c['id'] != DUP_ID]
    del data['companies'][DUP_COMPANY]
    data['merged'][DUP_ID] = SURVIVOR

    print(f'Удалена дублирующая карточка {DUP_ID} (-> {SURVIVOR}), профиль {DUP_COMPANY} снят')

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Записано.')
    else:
        print('(сухой прогон, для записи — --write)')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
