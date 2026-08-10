# -*- coding: utf-8 -*-
"""У карточки `gd4e555e3» («ЛУКОЙЛ-Коми приобрела у Газпром добыча
Краснодар 49% в СП ООО «Лаявожнефтегаз»») `seller` нёс «Газпром добыча
Краснодар 49% в СП ООО «Лаявожнефтегаз»» — хвост заголовка после предлога
«у» захвачен целиком вместо границы имени продавца (родня уже записанного
урока «заглавная буква сразу после предлога — плохая граница имени»).
Собственное поле `eco.share` этой же карточки называет продавца верно —
«ООО «Газпром добыча Краснодар»».

Почему не через review.py: `eco.share` — пересказ, написанный при более
раннем проходе, а не дословная цитата источника; в кэше притока текста для
этой карточки, подтверждающего его слово в слово, нет (часть источников не
отдаёт текст в этой сессии). Правка не добавляет факта — только чинит
границу уже присутствующего в базе имени.

Запуск: python3 pipeline/fix_lukoil_komi_seller_name.py
        python3 pipeline/fix_lukoil_komi_seller_name.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gd4e555e3'
OLD_SELLER = 'Газпром добыча Краснодар 49% в СП ООО «Лаявожнефтегаз»'
NEW_SELLER = 'Газпром добыча Краснодар'


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == CARD_ID)
    if card['seller'] == NEW_SELLER:
        print('УЖЕ ПРИМЕНЕНО %s' % CARD_ID)
        return
    assert card['seller'] == OLD_SELLER, '%s: seller уже другой' % CARD_ID
    print('ПРАВИМ  %s seller: «%s» -> «%s»' % (CARD_ID, OLD_SELLER, NEW_SELLER))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    card['seller'] = NEW_SELLER
    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
