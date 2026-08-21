# -*- coding: utf-8 -*-
"""Highland Gold/«Гейзер Голд» (`gd88cbe9a`): месячный дообыск нашёл
структуру собственности прежнего владельца лицензий (ООО «Гиперспэйс») —
кто такой Андрей Комаров в этой сделке и какими ещё горнодобывающими
активами он владеет. `eco.context` уже занято одним предложением про
«Гиперспэйс» как прежнего собственника — дословно объединить с этой
цитатой (из другого источника) `review.py` не может, правка разовым
скриптом.

Запуск: python3 pipeline/fix_highland_gold_geyser_context.py           # проверка
        python3 pipeline/fix_highland_gold_geyser_context.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gd88cbe9a'
OLD_CONTEXT = 'Прежним собственником «Гейзер Голд» было ООО «Гиперспэйс»'
NEW_CONTEXT = OLD_CONTEXT + (
    ', которое на 80,9% принадлежит АО «Старт» (19% владеет Андрей '
    'Комаров). «Гиперспэйс» также является собственником ООО «Варна '
    'Минералз» и ООО «Гора: Голден Ратио», в которое входят ООО '
    '«Желтугинская ГРК», ООО «Камчатская горная компания» и '
    '«Тихоокеанская горная компания». «Старту» принадлежит 100% долей '
    'ООО «Федорово Минералз».')
NEW_SRC = ['Золото и технологии', 'https://zolteh.ru/junior/'
           'khaylend-gold-priobrela-poiskovye-aktivy-na-kamchatke/']


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в базе' % CARD_ID
    assert card['eco'].get('context') == OLD_CONTEXT, (
        'eco.context изменился с ожидаемого: %r' % card['eco'].get('context'))
    src = card.setdefault('src', [])
    print('ПРАВИМ  %s: eco.context — структура собственности «Гиперспэйс»/Комаров' % CARD_ID)
    if write:
        card['eco']['context'] = NEW_CONTEXT
        if NEW_SRC not in src:
            src.append(NEW_SRC)
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('ЗАПИСАНО')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
