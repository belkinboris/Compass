# -*- coding: utf-8 -*-
"""ТГК-1/допэмиссия (g3c7dd2e2): собрание акционеров, вынесенное на 20 октября
2026 (событие уже в карточке), утвердило допэмиссию по закрытой подписке —
новый подтверждённый этап, не просто повтор уже известного «вынесено на
собрание».

Источник: ПРАЙМ, https://1prime.ru/20261022/tgk-1-874527531.html (забран в
кэш: data/inbox/raw/2026-10-22-articles.jsonl, «найден поиском»).

Без ключа — сухой прогон; запись — --write (файл перечитывается перед записью).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

EVENT = {
    'kind': 'approval',
    'date': '2026-10-22',
    'title': 'Собрание акционеров утвердило допэмиссию',
    'note': ('Акционеры ТГК-1 утвердили допэмиссию акций по закрытой подписке, '
              'которая практически удвоит уставный капитал компании, сообщила '
              'компания.'),
    'source': ['ПРАЙМ', 'https://1prime.ru/20261022/tgk-1-874527531.html'],
}


def main():
    write = '--write' in sys.argv
    data = json.load(open(DATA, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == 'g3c7dd2e2')
    events = card.setdefault('events', [])
    if any(e.get('kind') == EVENT['kind'] and e.get('date') == EVENT['date'] for e in events):
        print('g3c7dd2e2: такое событие уже есть')
        return 0
    print('g3c7dd2e2: добавляю событие %r' % EVENT['title'])
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    data = json.load(open(DATA, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == 'g3c7dd2e2')
    events = card.setdefault('events', [])
    if any(e.get('kind') == EVENT['kind'] and e.get('date') == EVENT['date'] for e in events):
        print('g3c7dd2e2: такое событие уже есть (перечитано перед записью)')
        return 0
    events.append(EVENT)
    new_src = ['ПРАЙМ', 'https://1prime.ru/20261022/tgk-1-874527531.html']
    if new_src not in card['src']:
        card['src'].append(new_src)
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('записано')
    return 0


if __name__ == '__main__':
    sys.exit(main())
