# -*- coding: utf-8 -*-
"""Тамбовский «Хогвартс» (geddb685d): начальная цена лота — «1 ₽» (символическая
цена повторного конкурса). `review.py` принимает сумму только в формате
«N млн|млрд ₽» (sum_is_supported), поэтому символический рубль пишется прямой
правкой — тот же путь, что у «Дома Сыромятниковых» (g896a22ba, см.
pipeline/archive/2026-10/fix_g896a22ba_title_not_source_headline_2026_10_23.py).
Тем же способом записано первое событие (`events[]` у карточки пуст).
Источник: https://abireg.ru/newsitem/118989-tambovskiy-khogvarts-vnov-vystavili-na-prodazhu-za-rubl/

Без ключа — сухой прогон; запись — --write (файл перечитывается перед записью).
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')

DEAL_ID = 'geddb685d'
SRC = ['Абирег', 'https://abireg.ru/newsitem/118989-tambovskiy-khogvarts-vnov-vystavili-na-prodazhu-za-rubl/']


NOTE = ('Региональный минимущества снова объявил конкурс на тот же лот: цена по-прежнему '
        'символическая, шаг торгов — 3,5 млн рублей, а задаток участника — 13,9 млн рублей. '
        'Заявки собирают до 3 декабря, а победителя назовут неделей позже, 10 декабря.')


def apply(data):
    n = 0
    for c in data['cards']:
        if c['id'] != DEAL_ID:
            continue
        if c.get('sum') == '1 ₽':
            c['sum'] = '1 ₽'
        else:
            assert c.get('sum') is None, (c['id'], c.get('sum'))
            c['sum'] = '1 ₽'
        c['eco']['sum'] = '1 ₽'
        c.setdefault('events', [])
        if not c['events']:
            c['events'].append({
                'kind': 'negotiations',
                'date': '2026-11-05',
                'title': 'Повторный конкурс объявлен',
                'note': NOTE,
                'source': SRC,
            })
        elif c['events'][0].get('note') != NOTE:
            c['events'][0]['note'] = NOTE
        n += 1
        print('%s: sum/eco.sum -> 1 ₽, events[0] записан' % c['id'])
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
