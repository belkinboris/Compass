# -*- coding: utf-8 -*-
"""Дом в Томске на торгах «Дом.РФ» (g5ee7977b): первое событие в `events[]`
(карточка без events — пишем прежний этап по той же схеме, что и у
geddb685d). Источник:
https://realty.ria.ru/20261106/tomsk-2129634207.html

Без ключа — сухой прогон; запись — --write (файл перечитывается перед записью).
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')

DEAL_ID = 'g5ee7977b'
SRC = ['РИА Недвижимость', 'https://realty.ria.ru/20261106/tomsk-2129634207.html']
NOTE = ('«Дом.РФ» объявил торги по деревянному дому в Томске: заявки принимаются до 30 '
        'ноября, а сам аукцион пройдет 4 декабря 2026 года.')


def apply(data):
    n = 0
    for c in data['cards']:
        if c['id'] != DEAL_ID:
            continue
        c.setdefault('events', [])
        if not c['events']:
            c['events'].append({
                'kind': 'negotiations',
                'date': '2026-11-06',
                'title': 'Торги объявлены',
                'note': NOTE,
                'source': SRC,
            })
            n += 1
            print('%s: events[0] записан' % c['id'])
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
