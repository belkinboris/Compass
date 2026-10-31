# -*- coding: utf-8 -*-
"""Карточка g29d48d22 («Дом.РФ»/КРТ Иркутская область): поле `sum` — финальная
цена аукциона не известна (только начальные цены лотов, см. eco.val), сумма
сделки ставится "Не раскрыта" — тот же литерал, что у 493 других карточек
базы; review.py принимает в `sum` только разобранные числовые форматы
(«N млн ₽» и т.п.), поэтому этот литерал пишется прямой правкой, как и у
прежних карточек с тем же значением.

Без ключа — сухой прогон; запись — --write.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')

CARD_ID = 'g29d48d22'
VALUE = 'Не раскрыта'


def main():
    write = '--write' in sys.argv
    data = json.load(open(PENDING, encoding='utf-8'))
    card = next(c for c in data['cards'] if c['id'] == CARD_ID)
    if card.get('sum') == VALUE:
        print('%s: sum уже установлен' % CARD_ID)
        return 0
    print('%s: sum %r -> %r' % (CARD_ID, card.get('sum'), VALUE))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    data = json.load(open(PENDING, encoding='utf-8'))
    card = next(c for c in data['cards'] if c['id'] == CARD_ID)
    if card.get('sum') == VALUE:
        print('%s: sum уже установлен (перечитано перед записью)' % CARD_ID)
        return 0
    card['sum'] = VALUE
    with open(PENDING, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('записано')
    return 0


if __name__ == '__main__':
    sys.exit(main())
