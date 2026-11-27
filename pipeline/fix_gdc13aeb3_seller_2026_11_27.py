# -*- coding: utf-8 -*-
"""gdc13aeb3 (очередь): продавец — «Акционеры Imperial Brands» (второе чтение, 27 ноября 2026).

Imperial Brands PLC — биржевая компания; предложение по Кодексу о поглощениях, если оно будет,
адресуется ее акционерам (заявление Altria: «considering a possible offer for Imperial Brands»;
ответ совета Imperial: «Shareholders are advised to take no action at this time»). Строка поста
«Продавец: не раскрыт» обманывала читателя. Правило — docs/card_parties.md, «Оферта всем
акционерам — продавец „Акционеры «<компания>»“» (решение владельца 6 ноября 2026); профиль не
заводится. В FIXES не ложится: русской дословной цитаты со словом «акционеры» в источниках нет.

    python3 pipeline/fix_gdc13aeb3_seller_2026_11_27.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
ID = 'gdc13aeb3'
NEW = 'Акционеры «Imperial Brands»'   # запись как у «Акционеры «Циана»» (check_post.py)
PREV = 'Акционеры Imperial Brands'    # первая запись этого же прогона, без кавычек
NOTE = 'продавцы — акционеры биржевой компании Imperial Brands PLC: предложение, если оно будет сделано, адресуется им всем. Крупного акционера искали в заявлениях Altria и Imperial Brands (RNS), у Reuters, РБК, «Ведомостей» и «Коммерсанта» — ни один источник его не называет. Британский реестр Companies House не открывали'


def main(write):
    data = json.load(open(PENDING, encoding='utf-8'))
    card = next(c for c in data['cards'] if c.get('id') == ID)
    if card.get('seller') == NEW and ((card.get('accepted_notes') or {}).get('no_profile') or {}).get('seller') == NOTE:
        print('уже применено'); return
    assert card.get('seller') in (None, PREV, NEW) and not card.get('seller_id'), card.get('seller')
    print('seller:', card.get('seller'), '->', NEW)
    if write:
        card['seller'] = NEW
        card['seller_src'] = 'text'
        notes = card.get('accepted_notes') or {}
        notes.setdefault('no_profile', {})['seller'] = NOTE
        card['accepted_notes'] = notes
        json.dump(data, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
