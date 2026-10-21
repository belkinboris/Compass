# -*- coding: utf-8 -*-
"""ЛУКОЙЛ/Carlyle (g20d4cc38): Минфин США (OFAC) продлил генеральную лицензию
на переговоры о продаже зарубежных активов ЛУКОЙЛа до 21 ноября 2026 года —
карточка уже отслеживает зависимость сделки от одобрения OFAC (`law.appr`) и
связку с переговорами по Украине (событие 2026-10-03); это очередное
продление того же разрешения, а не новый факт о самой сделке с Carlyle.

Источники: ТАСС (https://tass.ru/ekonomika/28239259), РИА Новости
(https://ria.ru/20261021/usa-2126060577.html).

Без ключа — сухой прогон; запись — --write (файл перечитывается перед записью).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

EVENT = {
    'kind': 'other',
    'date': '2026-10-21',
    'title': 'Лицензия OFAC на переговоры продлена',
    'note': ('Минфин США продлил генеральную лицензию, разрешающую переговоры о продаже '
              'зарубежных активов ЛУКОЙЛа, до 21 ноября 2026 года.'),
    'source': ['ТАСС', 'https://tass.ru/ekonomika/28239259'],
}


def main():
    write = '--write' in sys.argv
    data = json.load(open(DATA, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == 'g20d4cc38')
    events = card.setdefault('events', [])
    if any(e.get('kind') == EVENT['kind'] and e.get('date') == EVENT['date'] for e in events):
        print('g20d4cc38: такое событие уже есть')
        return 0
    print('g20d4cc38: добавляю событие %r' % EVENT['title'])
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    data = json.load(open(DATA, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == 'g20d4cc38')
    events = card.setdefault('events', [])
    if any(e.get('kind') == EVENT['kind'] and e.get('date') == EVENT['date'] for e in events):
        print('g20d4cc38: такое событие уже есть (перечитано перед записью)')
        return 0
    events.append(EVENT)
    new_src = ['РИА Новости', 'https://ria.ru/20261021/usa-2126060577.html']
    if new_src not in card['src']:
        card['src'].append(new_src)
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('записано')
    return 0


if __name__ == '__main__':
    sys.exit(main())
