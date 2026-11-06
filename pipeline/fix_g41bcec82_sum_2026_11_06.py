# -*- coding: utf-8 -*-
"""Палласовский рынок (g41bcec82): оценка доли — 22 929 000 ₽ («22 миллиона
929 тысяч рублей» в источнике — точное число, не круглые миллионы, поэтому
`review.py`/`sum_is_supported` не разбирает его форматом «N млн ₽»; пишем
точную сумму прямой правкой, тем же путем, что символический рубль у
geddb685d). Источник: https://v1.ru/text/gorod/2026/11/06/76748856/

Без ключа — сухой прогон; запись — --write (файл перечитывается перед записью).
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')

DEAL_ID = 'g41bcec82'
SUM = '22 929 000 ₽'


def apply(data):
    n = 0
    for c in data['cards']:
        if c['id'] != DEAL_ID:
            continue
        if c.get('sum') != SUM:
            assert c.get('sum') is None, (c['id'], c.get('sum'))
            c['sum'] = SUM
        c['eco']['sum'] = SUM
        n += 1
        print('%s: sum/eco.sum -> %s' % (c['id'], SUM))
    return n


def main(write):
    apply(json.load(open(PENDING, encoding='utf-8')))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    data = json.load(open(PENDING, encoding='utf-8'))
    if apply(data):
        with open(PENDING, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
