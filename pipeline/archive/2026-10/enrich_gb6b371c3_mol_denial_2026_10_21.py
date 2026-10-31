# -*- coding: utf-8 -*-
"""MOL/NIS (gb6b371c3): в тот же день, когда записали этап «подписано» со
слов и. о. вице-премьера Сербии Синиши Мали (событие `gb6b371c3-signed`),
сама MOL ответила заявлением на Будапештской бирже — не прямым отказом «не
подписывали», а обтекаемой биржевой формулировкой: существенных изменений,
которые нужно раскрывать рынкам капитала, не произошло. Это не опровержение
по существу (MOL не говорит, что Мали ошибся), но и не подтверждение — две
версии одного дня, обе с атрибуцией (docs/card_reading_pitfalls.md,
«Источники спорят или ошибаются»), статус карточки не меняется.

Источники: Ведомости
(https://www.vedomosti.ru/business/news/2026/10/21/1238886-mol-oprovergla),
РИА Новости (https://ria.ru/20261021/mol-2125929098.html).

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
    'title': 'MOL не подтвердила слова сербского вице-премьера',
    'note': ('MOL ответила на слова Мали биржевым заявлением: существенных изменений в '
              'переговорах, о которых нужно сообщать рынкам капитала, не произошло; если '
              'появятся значимые новости, компания раскроет их по закону. Прямо, что '
              'соглашение не подписано, MOL не говорит — это не опровержение по существу, '
              'а дежурная оговорка публичной компании.'),
    'source': ['Ведомости', 'https://www.vedomosti.ru/business/news/2026/10/21/1238886-mol-oprovergla'],
}


def main():
    write = '--write' in sys.argv
    data = json.load(open(DATA, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == 'gb6b371c3')
    events = card.setdefault('events', [])
    if any(e.get('kind') == EVENT['kind'] and e.get('date') == EVENT['date'] for e in events):
        print('gb6b371c3: такое событие уже есть')
        return 0
    print('gb6b371c3: добавляю событие %r' % EVENT['title'])
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    data = json.load(open(DATA, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == 'gb6b371c3')
    events = card.setdefault('events', [])
    if any(e.get('kind') == EVENT['kind'] and e.get('date') == EVENT['date'] for e in events):
        print('gb6b371c3: такое событие уже есть (перечитано перед записью)')
        return 0
    events.append(EVENT)
    new_src = ['РИА Новости', 'https://ria.ru/20261021/mol-2125929098.html']
    if new_src not in card['src']:
        card['src'].append(new_src)
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('записано')
    return 0


if __name__ == '__main__':
    sys.exit(main())
