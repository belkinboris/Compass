# -*- coding: utf-8 -*-
"""«1С»/«Райтек» (g685f1e39): карточка застряла с типом «M&A» без единой
стороны — docs/card_parties.md уже отмечал ее как пример СП, повисшего без
профилей и без поста. Заголовок и источник (CNews, 22 сентября 2026) прямо
говорят о создании совместного предприятия, а не о покупке доли, поэтому
тип меняется на «Создание СП» (docs/card_status_dates.md) — остальное
(профили участников buyer/target, проза) добавляется следующим шагом через
review.py/accept_card.py. `no_parties` был объяснением для типа «M&A»
(«продажи доли нет») — у СП своя логика (участники, а не продавец), поле
снимается как устаревшее.

Без ключа — сухой прогон; запись — --write (файл перечитывается перед записью).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def main():
    write = '--write' in sys.argv
    data = json.load(open(DATA, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == 'g685f1e39')
    assert card['type'] == 'M&A', card['type']
    assert not card.get('buyer') and not card.get('target') and not card.get('seller_id')
    assert card.get('no_parties') == 'Создание совместного предприятия, продажи доли нет'
    card['type'] = 'Создание СП'
    del card['no_parties']
    print('g685f1e39: type M&A -> Создание СП; no_parties снят')
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('записано')
    return 0


if __name__ == '__main__':
    sys.exit(main())
