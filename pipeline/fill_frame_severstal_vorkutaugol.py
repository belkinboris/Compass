# -*- coding: utf-8 -*-
"""У карточки `g66cb145a` («Продажа «Северсталью» 100% АО «Воркутауголь»
группе «Русская Энергия»») `buyer` был `None`, хотя нужный профиль уже есть
в базе — `g5d22aa06` («ООО «Группа Русская энергия»», прямо описан как
«Холдинговая компания, владеющая угледобывающим АО «Воркутауголь»»); это
не тот же профиль, что `gee90a2b1` («Русская энергия», отрасль
«Недвижимость») — омоним, к этой сделке отношения не имеющий.

Запуск: python3 pipeline/fill_frame_severstal_vorkutaugol.py
        python3 pipeline/fill_frame_severstal_vorkutaugol.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g66cb145a'
BUYER_ID = 'g5d22aa06'


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == CARD_ID)
    if card.get('buyer') == BUYER_ID:
        print('УЖЕ ПРИМЕНЕНО %s' % CARD_ID)
        return
    assert card.get('buyer') is None, '%s: buyer уже задан' % CARD_ID
    print('ПРАВИМ  %s: buyer=%s (ООО «Группа Русская энергия»)' % (CARD_ID, BUYER_ID))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    card['buyer'] = BUYER_ID
    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
