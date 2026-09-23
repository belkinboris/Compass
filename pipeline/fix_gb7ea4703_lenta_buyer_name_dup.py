# -*- coding: utf-8 -*-
"""23 сентября 2026, карточка gb7ea4703 («Лента»/«Мария-Ра»): у покупателя
одновременно стояли ссылка на профиль (`buyer` = gcca31da7, «Группа Лента»)
и текстовое имя (`buyer_name` = «Лента») — `test_buyer_is_named_once` не
пропускает такую пару, потому что при следующей правке одного поля другое
разойдётся с ним. `link_parties.py` не увидел карточку, потому что `buyer`
у неё уже был проставлен раньше (сторож поля `('buyer',)` в ROLES не даёт
дважды привязывать одну роль) — обычная чистка `card.pop('buyer_name')`
внутри `link_card()` сработала бы только при СВЕЖЕЙ привязке, здесь её
делаем той же логикой отдельно, вручную.

Запуск: python3 pipeline/fix_gb7ea4703_lenta_buyer_name_dup.py --write
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == 'gb7ea4703')
    assert card.get('buyer') == 'gcca31da7', card.get('buyer')
    assert card.get('buyer_name') == '«Лента»', card.get('buyer_name')
    print('ДО:  buyer=%r buyer_name=%r' % (card.get('buyer'), card.get('buyer_name')))
    card.pop('buyer_name', None)
    print('ПОСЛЕ: buyer=%r buyer_name=%r' % (card.get('buyer'), card.get('buyer_name')))
    if write:
        json.dump(data, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print('Записано.')
    else:
        print('Сухой прогон. Запись — с ключом --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
