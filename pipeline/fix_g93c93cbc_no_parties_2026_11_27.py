# -*- coding: utf-8 -*-
"""Карточка g93c93cbc (очередь pending.json, приток 27 ноября 2026): дорожные
компании Челябинской области обращены в доход государства.

`no_parties` — служебная формулировка, одна у всех карточек изъятия по суду
(см. pipeline/archive/2026-11/fix_logvinenko_no_parties_2026_11_26.py), поэтому
пишется разовым скриптом, а не таблицей FIXES. Покупателя и продавца нет: доли
изъяты судом у ответчиков-граждан (74.ru, URA.RU, 27.11.2026); кому они
переданы (Росимущество) — ни один источник не называет, только «в доход
государства».

Запуск: python3 pipeline/fix_g93c93cbc_no_parties_2026_11_27.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')
CARD_ID = 'g93c93cbc'
NO_PARTIES = 'Изъятие по решению суда: покупателя и продавца нет, актив перешел государству.'


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))   # читаем прямо перед записью
    card = next(c for c in data['cards'] if c['id'] == CARD_ID)
    if card.get('no_parties') == NO_PARTIES:
        print('уже записано')
        return 0
    assert card.get('no_parties') is None, card.get('no_parties')
    assert card.get('buyer') is None and card.get('seller') is None
    card['no_parties'] = NO_PARTIES
    if write:
        json.dump(data, open(PATH, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('ЗАПИСАНО: no_parties для %s' % CARD_ID)
    else:
        print('Сухой прогон. no_parties -> %r' % NO_PARTIES)
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
