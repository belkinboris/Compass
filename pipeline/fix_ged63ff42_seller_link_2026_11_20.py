# -*- coding: utf-8 -*-
"""Карточка ged63ff42 (ФРТ/«Гольяново парк», Балашиха): продавец текстом
«Фонд развития территорий» совпадает с уже существующим профилем g6921da17
(«ППК «Фонд развития территорий»», ИНН 7704446429 подтвержден в
fns_registry.py на карточке gba764f10 — тот же госфонд, тот же класс
сделки). Связываем seller_id сразу, а не оставляем приемке: точное
совпадение имени не сработает само (`link_parties.company_key` снимает
«ооо/оао/зао/пао/ао/нао/гк/пкф/тд», но не «ппк» — префикс остается, ключи
«фондразвитиятерриторий» и «ппкфондразвитиятерриторий» не совпадают). Этот
же пробел уже завел дубль профиля на gba764f10, который потом сносили
отдельным скриптом (archive/2026-10/fix_frt_dedupe_profile_2026_10_16.py).

Без ключа — сухой прогон, запись — --write.
"""
import json
import sys

PENDING = '/home/user/Compass/static/data/pending.json'
DATA = '/home/user/Compass/static/data/deals_promoted.json'
CARD_ID = 'ged63ff42'
SELLER_ID = 'g6921da17'
SELLER_TEXT = 'Фонд развития территорий'


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    assert SELLER_ID in data['companies'], '%s пропал из companies' % SELLER_ID
    pending = json.load(open(PENDING, encoding='utf-8'))
    card = {c['id']: c for c in pending['cards']}[CARD_ID]
    assert card.get('seller') == SELLER_TEXT, 'seller уже другой: %r' % card.get('seller')
    assert card.get('seller_id') is None, 'seller_id уже %r' % card.get('seller_id')
    print('%s: seller_id None -> %r (%s)' % (CARD_ID, SELLER_ID, data['companies'][SELLER_ID]['name']))
    if not write:
        print('Сухой прогон. Применение — с ключом --write.')
        return 0
    fresh = json.load(open(PENDING, encoding='utf-8'))
    fc = {c['id']: c for c in fresh['cards']}[CARD_ID]
    assert fc.get('seller_id') is None, 'seller_id поменяли параллельно — перечитайте'
    fc['seller_id'] = SELLER_ID
    with open(PENDING, 'w', encoding='utf-8') as f:
        json.dump(fresh, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('Применено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
