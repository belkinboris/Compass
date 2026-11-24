# -*- coding: utf-8 -*-
"""Карточка g9b4c2e71 («Т-Технологии»/«Циан»): 24 ноября 2026 группа
направила акционерам формальную оферту (срок принятия 25.11.2026-24.02.2027).
Это новый этап переговоров (не согласование/закрытие/срыв — kind остается
'negotiations', milestones.POSTWORTHY_MILESTONE_KINDS его не включает),
дописывается в events[] структурной правкой, не через review.py (events
не входит в его таблицу FIXES).

Источник: Абирег,
https://abireg.ru/newsitem/119535-t-tekhnologii-napravili-ofertu-na-vykup-tsiana-po-993-05-rublya-za-aktsiyu/

Запуск:
    python3 pipeline/fix_g9b4c2e71_add_oferta_event_2026_11_24.py            # сухой прогон
    python3 pipeline/fix_g9b4c2e71_add_oferta_event_2026_11_24.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, '..', 'static', 'data', 'deals_promoted.json')
CARD_ID = 'g9b4c2e71'
URL = 'https://abireg.ru/newsitem/119535-t-tekhnologii-napravili-ofertu-na-vykup-tsiana-po-993-05-rublya-za-aktsiyu/'

NEW_EVENT = {
    'kind': 'negotiations',
    'date': '2026-11-24',
    'title': 'Переговоры',
    'note': ('«Т-Технологии» направили «Циану» формальную оферту на выкуп до 100% акций по 993,05 '
             'рубля за бумагу; срок принятия — с 25 ноября 2026 года по 24 февраля 2027 года. Совет '
             'директоров «Циана» 24 ноября рассмотрел создание специального комитета для '
             'предварительной оценки предложения.'),
    'source': ['Абирег', URL],
}


def apply(data):
    card = next(c for c in data['deals'] if c['id'] == CARD_ID)
    events = card.setdefault('events', [])
    assert not any(e.get('date') == NEW_EVENT['date'] and e.get('kind') == NEW_EVENT['kind']
                   for e in events), 'событие на эту дату уже есть'
    events.append(NEW_EVENT)


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    apply(data)
    print('событие добавлено: %s %s' % (NEW_EVENT['date'], NEW_EVENT['title']))
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
