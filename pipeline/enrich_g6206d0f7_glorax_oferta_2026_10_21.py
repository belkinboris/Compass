# -*- coding: utf-8 -*-
"""GloraX (g6206d0f7, IPO 31.10.2025): год назад при размещении компания дала
безотзывную публичную оферту — если через год котировки окажутся ниже цены
IPO, GloraX выкупит бумаги у инвесторов IPO по цене размещения +19,5%
(условие уже описано в `eco.share` этой же карточки). 21 октября 2026 это
условие сработало: акция торгуется ниже 64 ₽, и дочерняя структура «Антарес»
разместила оферту. Это не новая сделка с новыми сторонами — тот же предмет
(акции GloraX) и тот же механизм, обещанный при самом IPO, — поэтому пишем
как этап (`events`) этой же карточки, а не отдельной карточкой
(docs/intake_run.md о «новом этапе той же истории»).

Источники: Ведомости
(https://www.vedomosti.ru/investments/news/2026/10/21/1238774-glorax-razmestil),
Frank Media (https://frankmedia.ru/311172).

Без ключа — сухой прогон; запись — --write (файл перечитывается перед записью).
"""
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

EVENT = {
    'kind': 'announced',
    'date': '2026-10-21',
    'title': 'Безотзывная оферта на выкуп акций размещена',
    'note': ('Обещанная при размещении оферта сработала: акция торгуется ниже цены IPO '
              '(64 ₽), и застройщик «Антарес» (дочерняя структура «Глоракса») выставил '
              'выкуп по 76,48 ₽ за акцию — это та самая премия 19,5%, на которую инвесторы '
              'могли рассчитывать по условиям IPO. Продать бумаги могут те, кто владел '
              'ими без перерыва весь год с начала торгов, но не больше 30 000 акций на '
              'одного инвестора.'),
    'source': ['Ведомости', 'https://www.vedomosti.ru/investments/news/2026/10/21/1238774-glorax-razmestil'],
}


def main():
    write = '--write' in sys.argv
    data = json.load(open(DATA, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == 'g6206d0f7')
    events = card.setdefault('events', [])
    if any(e.get('kind') == EVENT['kind'] and e.get('date') == EVENT['date'] for e in events):
        print('g6206d0f7: такое событие уже есть')
        return 0
    events.append(EVENT)
    card['src'].append(['Frank Media', 'https://frankmedia.ru/311172'])
    print('g6206d0f7: добавлено событие %r' % EVENT['title'])
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    data = json.load(open(DATA, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == 'g6206d0f7')
    events = card.setdefault('events', [])
    if any(e.get('kind') == EVENT['kind'] and e.get('date') == EVENT['date'] for e in events):
        print('g6206d0f7: такое событие уже есть (перечитано перед записью)')
        return 0
    events.append(EVENT)
    if ['Frank Media', 'https://frankmedia.ru/311172'] not in card['src']:
        card['src'].append(['Frank Media', 'https://frankmedia.ru/311172'])
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('записано')
    return 0


if __name__ == '__main__':
    sys.exit(main())
