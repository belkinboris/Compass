# -*- coding: utf-8 -*-
"""Карточка gb1efa21d (Selectel купил M1Cloud): NSP — юридический консультант
покупателя; пост в источники. Найдено проверкой снятых дублей 6 ноября 2026:
пост https://t.me/LawFirms/11405 (18 сентября 2026) лежал в hold/*-enrich.json
слабым совпадением и в карточку не попал — тот же случай, что BIRCH/Swordfish.
Цитата: «АБ NSP сообщает: NSP сопровождало облачного провайдера Selectel в
сделке по приобретению компании M1Cloud (ООО "Стек Групп")».

    python3 pipeline/archive/2026-11/fix_gb1efa21d_nsp_2026_11_06.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
CARD_ID = 'gb1efa21d'
URL = 'https://t.me/LawFirms/11405'
ROW = ['Консультант покупателя', 'NSP',
       'Юридический консультант Selectel: структура сделки и вся документация, включая договор '
       'купли-продажи долей ООО «Стек Групп» (M1Cloud). Источник: t.me/LawFirms/11405']
SRC = ['РУЛЬФЫ, ИЛЬФЫ И ИНХАУСЫ (@LawFirms)', URL]


def apply(base):
    card = next(d for d in base['deals'] if d['id'] == CARD_ID)
    adv = card['law']['adv']
    assert adv == [], adv
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
