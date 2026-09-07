# -*- coding: utf-8 -*-
"""Карточка g10bfcb70 (ЦИУПС/ТЦ «Родник» и «Алмаз», приток 7 сентября 2026,
13:20): единственное событие в `events` несло дату ингеста (2026-09-07)
вместо даты торгов (2026-08-06, уже исправленной в верхнеуровневом `date`
через review.py) и текст с сырым вики-мусором TAdviser («История 2026:
«Центр...» купил ТЦ «Родник» «Компания:ЦИУПС...»») вместо связного
предложения.

`review.py`'s get_field/set_field не поддерживают индексацию списков
(`events.0.date`), поэтому дата и текст этапа правятся здесь, а не через
таблицу FIXES — родня уже описанного в CLAUDE.md класса правок вне
review.py (обрубленные `events[].note`).

Запуск: python3 pipeline/fix_ciups_rodnik_almaz_event_date_note.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING_PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')

CARD_ID = 'g10bfcb70'
OLD_DATE = '2026-09-07'
NEW_DATE = '2026-08-06'
OLD_NOTE_PREFIX = 'История 2026:'
NEW_NOTE = ('ООО «Центр инжиниринговых услуг при проектировании и '
             'строительстве» (ЦИУПС) стало победителем торгов по продаже '
             'ранее входивших в группу «Макфа» компаний «Родник» и УК '
             '«Содействие», на балансе которых находятся два крупных '
             'торгово-развлекательных комплекса в Челябинске – «Родник» '
             'общей площадью 126 000 кв. м и «Алмаз» на 212 000 кв. м.')


def main(write=False):
    with open(PENDING_PATH, encoding='utf-8') as f:
        pending = json.load(f)

    matches = [c for c in pending['cards'] if c['id'] == CARD_ID]
    assert len(matches) == 1, f'ожидалась ровно одна карточка {CARD_ID}, найдено {len(matches)}'
    card = matches[0]
    events = card.get('events') or []
    assert len(events) == 1, events
    ev = events[0]
    assert ev.get('date') == OLD_DATE, ev.get('date')
    assert (ev.get('note') or '').startswith(OLD_NOTE_PREFIX), ev.get('note')

    ev['date'] = NEW_DATE
    ev['note'] = NEW_NOTE

    print(f'Дата этапа {OLD_DATE} -> {NEW_DATE}, текст этапа заменён на связное предложение.')

    if write:
        with open(PENDING_PATH, 'w', encoding='utf-8') as f:
            json.dump(pending, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Записано.')
    else:
        print('(сухой прогон, для записи — --write)')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
