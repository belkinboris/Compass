# -*- coding: utf-8 -*-
"""Приемка g9550db70 (помещение бильярдного клуба «Пирамида Тюмень»):
анонимное объявление о продаже на доске бесплатных объявлений не называет
ни имя продавца, ни юрлицо, ни покупателя (покупателя для сделки, которая
еще не состоялась, не бывает). Причина пустых сторон (`no_parties`) — по
аналогии с gb4937a72 (завод по производству скотча в Тюменской области,
тот же день, archive/2026-11/fix_gb4937a72_no_parties_2026_11_23.py) и
g8e9d37ba («Объект только выставлен на продажу: покупателя нет...»).

Через review.py не проводится: `no_parties` — не факт из цитаты, а
объяснение пустоты поля, а механическая проверка review.check для
произвольного текста требует дословную цитату — это не тот случай
(docs/card_editing_scripts.md).

Разовый, со сборкой assert на прежнее состояние. Запуск:
    python3 pipeline/fix_add_piramida_tyumen_no_parties_2026_11_23.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PENDING = os.path.join(ROOT, '..', 'static', 'data', 'pending.json')
CARD_ID = 'g9550db70'

NOTE = ('Объявление о продаже на площадке бесплатных объявлений: автор не называет '
        'ни свое имя, ни юрлицо клуба. Покупателя нет — сделка не состоялась, '
        'это предложение продавца.')


def main(write=False):
    data = json.load(open(PENDING, encoding='utf-8'))
    card = next((c for c in data['cards'] if c.get('id') == CARD_ID), None)
    if card is None:
        print('карточка %s не найдена в pending.json — уже промоутнута?' % CARD_ID)
        return 1
    assert card.get('no_parties') is None, 'no_parties уже стоит: %r' % card.get('no_parties')
    print('ПИШУ no_parties =', NOTE)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    card['no_parties'] = NOTE
    json.dump(data, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv[1:]))
