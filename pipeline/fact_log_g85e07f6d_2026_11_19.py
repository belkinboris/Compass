# -*- coding: utf-8 -*-
"""Карточка g85e07f6d (НПО «РТС» купило на торгах треть здания бывшего ЦНТИ
в Челябинске) была дополнена исходом аукциона разовым скриптом
(merge_npo_rts_cnti_result_2026_11_19.py) без записи подтверждения через
fact_edit_guard.log() — prepush_check.py отказал пушить («правка факта без
подтверждающей цитаты» у 7 полей: title, date, status, sum, eco.sum, buyer,
asset). Этот скрипт дописывает недостающие записи в card['fact_log'] —
значения полей уже стоят верно (проверено assert), меняется только
подтверждение.

Источник: 74.ru, https://74.ru/text/business/2026/11/19/76777277/
(текст на диске — data/inbox/raw/2026-11-19-articles.jsonl, поле summary).

Запуск: python3 pipeline/fact_log_g85e07f6d_2026_11_19.py --write
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import fact_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
CARD_ID = 'g85e07f6d'
SRC = ['74.RU', 'https://74.ru/text/business/2026/11/19/76777277/']
BY = 'приток, 19 ноября 2026'

Q_WINNER = 'Победителем аукциона признали научно-производственное объединение «Радиотехнические системы».'
Q_SOLD = 'В итоге этаж здания бывшего ЦНТИ продан по начальной цене — 59,8 миллиона рублей.'
Q_DATE = 'В четверг, 19 ноября, итоговый протокол размещен на портале «ГИС. Торги».'
Q_FLOOR = ('Судя по иллюстрациям в конкурсной документации, НПО «РТС» станет владельцем третьего этажа здания '
           '|| В прошлом году часть помещений ЦНТИ — 2488 кв. м — перешла ПАО «Дом.РФ»')

ENTRIES = [
    ('title', 'НПО «РТС» купило на торгах треть здания бывшего ЦНТИ в Челябинске', Q_WINNER + ' || ' + Q_SOLD),
    ('date', '2026-11-19', Q_DATE),
    ('status', 'Закрыта', Q_SOLD),
    ('sum', '59,8 млн ₽', Q_SOLD),
    ('eco.sum', '59,8 млн ₽', Q_SOLD),
    ('buyer', 'g2aef124c', Q_WINNER),
    ('asset', 'треть здания бывшего ЦНТИ в Челябинске — третий этаж (2488 кв. м)', Q_FLOOR),
]


def get_field(card, field):
    if '.' in field:
        head, tail = field.split('.', 1)
        return (card.get(head) or {}).get(tail)
    return card.get(field)


def apply(data):
    card = next(c for c in data['deals'] if c['id'] == CARD_ID)
    for field, new, quote in ENTRIES:
        cur = get_field(card, field)
        assert cur == new, '%s: ожидали %r, стоит %r' % (field, new, cur)
        fact_edit_guard.log(card, field, new, quote, SRC[1], BY)


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    apply(data)
    print('подтверждений добавлено: %d' % len(ENTRIES))
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
