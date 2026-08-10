# -*- coding: utf-8 -*-
"""У карточки `gdffd613c` («Братья Бабаевы и топ-менеджеры приобрели
контрольный пакет АО «Вектор Рейл»... у Тайчера и Смыслова») `seller` нёс
«Тайчера и Смыслова» — родительный падеж, оставшийся от заголовка («у
Тайчера и Смыслова»), тогда как поле продавца показывается как
самостоятельное имя и должно стоять в именительном. Собственное
`eco.rationale» этой же карточки уже называет обе фамилии верно —
«Продавцы — Алексей Тайчер и Сергей Смыслов».

Почему не через review.py: текст rationale — пересказ, написанный при
более раннем проходе, не дословная цитата источника в кэше притока (нет
файла с этим текстом слово в слово).

Запуск: python3 pipeline/fix_vector_rail_seller_case.py
        python3 pipeline/fix_vector_rail_seller_case.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gdffd613c'
OLD_SELLER = 'Тайчера и Смыслова'
NEW_SELLER = 'Алексей Тайчер и Сергей Смыслов'


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
