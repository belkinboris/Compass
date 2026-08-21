# -*- coding: utf-8 -*-
"""Связывает `buyer_name` карточки HeadHunter/Happy Job (gebead2e8) с уже
существующим профилем «HeadHunter» (g0029735f, уже buyer у 2 других
сделок в базе) — та же граница, что в `link_named_parties_to_existing_
profiles.py` (точное совпадение нормализованного имени), но точечно:
общий скрипт спотыкается на устаревшем состоянии другой, не связанной с
этой правкой карточки (`g097e34b2.seller_id` заполнено с 18 августа, а
жёсткий список кандидатов скрипта — нет).

Запуск:
    python3 pipeline/fix_headhunter_happyjob_buyer_link.py            # проверка
    python3 pipeline/fix_headhunter_happyjob_buyer_link.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == 'gebead2e8')
    assert card.get('buyer_name') == 'HeadHunter', 'buyer_name изменился'
    assert not card.get('buyer'), 'buyer уже заполнено'
    assert data['companies'].get('g0029735f', {}).get('name') == 'HeadHunter', \
        'профиль g0029735f больше не называется HeadHunter'
    print('ПРАВИМ  gebead2e8: buyer_name=%r -> buyer=g0029735f' % card['buyer_name'])
    if write:
        card['buyer'] = 'g0029735f'
        card['buyer_name'] = None
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('ЗАПИСАНО')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
