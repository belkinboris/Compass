# -*- coding: utf-8 -*-
"""Профиль ДОМ.РФ (gb2b066c3): имя «АО «ДОМ.РФ»» устарело — с сентября 2025 года общество
публичное (об этом говорит и описание профиля, и `legal_short`, и сайт самого ДОМ.РФ:
«ПАО ДОМ.РФ (ИНН 7729355614, ОГРН 1027700262270)»). Находка второго чтения карточки gb88e1cdc
27 ноября 2026: в посте продавец показан как АО. Близнецов нет — профиль ДОМ.РФ в базе один;
тот же id, сделки и адреса не меняются.

Без ключа — сухой прогон; запись — --write.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CID = 'gb2b066c3'
OLD = 'АО «ДОМ.РФ»'
NEW = 'ПАО «ДОМ.РФ»'


def main(write):
    # файл читается прямо перед записью: чужой пуш не затирается старым снимком
    data = json.load(open(DATA, encoding='utf-8'))
    comp = data['companies'][CID]
    if comp['name'] == NEW:
        print('уже применено')
        return 0
    assert comp['name'] == OLD, comp['name']
    assert comp.get('legal_short') == NEW, comp.get('legal_short')
    comp['name'] = NEW
    print('%s: name %r -> %r' % (CID, OLD, NEW))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
