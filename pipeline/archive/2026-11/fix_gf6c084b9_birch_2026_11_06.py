# -*- coding: utf-8 -*-
"""Карточка gf6c084b9 (ЗПИФ «ВИМ Инвестиций» / Swordfish Security): BIRCH —
юридический консультант покупателя, и пост BIRCH — в источники.

6 ноября 2026 владелец отметил «это сделка» пост BIRCH о своей роли, рутина
сняла карточку из него как дубль «без единого нового факта» и ответила
владельцу «новое из новости добавлено в ту карточку». На деле не добавлено
ничего, а новый факт был: в карточке назван только консультант продавца
(ALUMNI Partners), консультант покупателя — нет. law.adv — список, review.py
его не пишет (тот же случай — fix_g13f5c85b_law_adv_remain_2026_11_06.py).

Источник: https://t.me/BIRCHLEGAL/2343 — «Корпоративная / M&A практика BIRCH
выступила юридическим консультантом в рамках сделки по приобретению ЗПИФ под
управлением АО ВИМ Инвестиции миноритарной доли в ГК Swordfish Security».

    python3 pipeline/archive/2026-11/fix_gf6c084b9_birch_2026_11_06.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
CARD_ID = 'gf6c084b9'
URL = 'https://t.me/BIRCHLEGAL/2343'
ROW = ['Консультант покупателя', 'BIRCH',
       'Корпоративная / M&A практика BIRCH консультировала покупателя — ЗПИФ под управлением '
       'АО «ВИМ Инвестиции». Источник: t.me/BIRCHLEGAL/2343']
SRC = ['BIRCH (Telegram)', URL]


def apply(base):
    card = next(d for d in base['deals'] if d['id'] == CARD_ID)
    adv = card['law']['adv']
    assert [r[1] for r in adv] == ['ALUMNI Partners'], adv
    assert URL not in json.dumps(card['src']), 'источник уже есть'
    adv.append(ROW)
    card['src'].append(SRC)
    return card


def main(argv):
    write = '--write' in argv
    base = json.load(open(BASE, encoding='utf-8'))
    card = apply(base)
    print('%s: + %s; + источник %s' % (CARD_ID, ROW[:2], URL))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    base = json.load(open(BASE, encoding='utf-8'))   # перечитать прямо перед записью
    apply(base)
    with open(BASE, 'w', encoding='utf-8') as f:
        json.dump(base, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
