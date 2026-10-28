# -*- coding: utf-8 -*-
"""g31831238 (Intel/Classiq): sum_fields_differ — eco.sum был прозой источника,
а sum несёт канонический формат с пометкой «(по оценке)»; docs/card_money.md:
«это одна и та же цена в двух местах карточки — синхронизировать оба поля
одним значением». Атрибуция (Bloomberg) остаётся в eco.val, своими словами.

Запуск: python3 pipeline/fix_g31831238_eco_sum_sync.py [--write]
"""
import json
import sys

PATH = 'static/data/pending.json'
OLD = 'Оценивается примерно в $2,3 млрд'
NEW = '$2,3 млрд (по оценке)'


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    card = next(c for c in data['cards'] if c['id'] == 'g31831238')
    assert card['eco']['sum'] == OLD, card['eco']['sum']
    assert card['sum'] == NEW, card['sum']
    if not write:
        print('сухой прогон: eco.sum %r -> %r' % (OLD, NEW))
        return
    data = json.load(open(PATH, encoding='utf-8'))
    card = next(c for c in data['cards'] if c['id'] == 'g31831238')
    assert card['eco']['sum'] == OLD, card['eco']['sum']
    card['eco']['sum'] = NEW
    json.dump(data, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('записано: eco.sum -> %r' % NEW)


if __name__ == '__main__':
    main('--write' in sys.argv)
