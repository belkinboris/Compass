# -*- coding: utf-8 -*-
"""g46c6e23f («Яндекс»/Boxberry) — старое нарушение правил текста (text_rules.py,
шаг 6 рутины «качество»): примечание первого события несло издание в скобках
«(Интерфакс, 16 апреля 2025 года)» вместо названия издания в самом тексте.

ПОЧЕМУ НЕ ЧЕРЕЗ review.py. Поле `events[0].note` — элемент списка, а
`review.py`'s `get_field`/`set_field` обходят только вложенные словари по
точке в пути («eco.val», «law.appr») и возвращают None на числовом индексе
списка — правка через обычную запись FIXES отказывает «поле уже другое: в
базе None». Факт не меняется (то же событие, тот же источник, та же дата),
меняется только формулировка — одноразовый скрипт с `assert` на старое
значение.

Источник (interfax.ru/business/1021099, 16.04.2025): «Москва. 16 апреля.
INTERFAX.RU - "Яндекс" объявил о приобретении службы доставки Boxberry.»

Запуск:
    python3 pipeline/fix_g46c6e23f_event_note_2026_11_24.py            # сухой прогон
    python3 pipeline/fix_g46c6e23f_event_note_2026_11_24.py --write    # записать
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'
DEAL_ID = 'g46c6e23f'
OLD_NOTE = '«Яндекс» сообщил о покупке службы доставки Boxberry (Интерфакс, 16 апреля 2025 года).'
NEW_NOTE = 'Интерфакс сообщил 16 апреля 2025 года, что «Яндекс» объявил о покупке службы доставки Boxberry.'


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    deal = by_id.get(DEAL_ID)
    assert deal is not None, 'нет сделки %s' % DEAL_ID
    events = deal.get('events') or []
    assert events, 'нет events у %s' % DEAL_ID
    current = events[0].get('note')
    if current == NEW_NOTE:
        print('Уже применено.')
        return
    assert current == OLD_NOTE, 'events[0].note неожиданное: %r' % current

    print('%s: events[0].note %r -> %r' % (DEAL_ID, current, NEW_NOTE))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    events[0]['note'] = NEW_NOTE
    assert events[0]['note'] == NEW_NOTE

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
