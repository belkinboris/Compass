# -*- coding: utf-8 -*-
"""Карточка g9b852635 (Эталон/Нагатинская пойма): второе чтение нашло, что
заголовок пишет сумму словом («8,1 млрд рублей»), а везде внутри карточки
(sum/eco.val/пост) — знаком («8,1 млрд ₽») — приводит заголовок к тому же
знаку, цифра не меняется.

Запуск:
    python3 pipeline/fix_g9b852635_title_currency_2026_11_24.py            # сухой прогон
    python3 pipeline/fix_g9b852635_title_currency_2026_11_24.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, '..', 'static', 'data', 'deals_promoted.json')
CARD_ID = 'g9b852635'
OLD = 'Участки «Эталона» в Нагатинской пойме выставлены на продажу за 8,1 млрд рублей'
NEW = 'Участки «Эталона» в Нагатинской пойме выставлены на продажу за 8,1 млрд ₽'


def apply(data):
    card = next(c for c in data['deals'] if c['id'] == CARD_ID)
    assert card['title'] == OLD, 'заголовок уже изменен кем-то другим'
    card['title'] = NEW


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    apply(data)
    print('title обновлен:', NEW)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    data = json.load(open(DATA, encoding='utf-8'))
    apply(data)
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main('--write' in sys.argv[1:]))
