"""Ситибанк: ALUMNI Partners — регуляторный консультант покупателя (14 ноября 2026).

Владелец: «в сделке Сити нужно у Alumni подписать, что это не юридический
консультант, а регуляторный»; в статистике фирма остается юридической.
Без ключа — сухой прогон, запись по --write.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
OLD = 'Консультант покупателя по регуляторным согласованиям («Ренессанс Капитал»)'
NEW = 'Регуляторный консультант покупателя («Ренессанс Капитал»)'


def main(write):
    base = json.load(open(BASE, encoding='utf-8'))      # читается прямо перед записью
    deal = next(d for d in base['deals'] if d['id'] == 'citibank')
    rows = [r for r in deal['law']['adv'] if len(r) > 1 and r[1] == 'ALUMNI Partners']
    assert len(rows) == 1 and rows[0][0] == OLD, rows
    rows[0][0] = NEW
    print('citibank: ALUMNI Partners —', OLD, '→', NEW)
    if write:
        json.dump(base, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
