# -*- coding: utf-8 -*-
"""Приток 23 сентября 2026, карточка g4b00b18e: заметка события обрывалась
многоточием на середине слова. Прямая правка (не через review.py FIXES) —
тем же способом, каким уже чинилась заметка события на gffe3c2d0/g076af76a
в этой же сессии.

Запуск: python3 pipeline/fix_paradiz_event_note_2026_09_23.py --write
"""
import argparse
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')

CARD_ID = 'g4b00b18e'

NEW_NOTE = (
    'Московские власти 14 сентября 2026 года продали помещение площадью 3,06 тыс. '
    'кв. м в здании кинотеатра «Пять звезд» на улице Бахрушина в центре столицы. '
    'Новым владельцем стала структура кинокомпании «Парадиз» — ООО «Кинокомпания '
    '«Парадиз продакшнз»»; ранее у компании была только 1 тыс. кв. м в этом здании, '
    'и теперь она консолидировала весь объект на 4 тыс. кв. м. Цену выкупа — '
    '438,9 млн ₽ — установил Арбитражный суд Москвы в споре о стоимости между '
    'департаментом городского имущества и «Парадизом».'
)


def main(write):
    data = json.load(open(PENDING, encoding='utf-8'))
    card = next(c for c in data['cards'] if c['id'] == CARD_ID)
    events = card.get('events') or []
    assert events and events[0]['note'].endswith('имущества…'), 'заметка события уже не та, что ожидали'
    events[0]['note'] = NEW_NOTE
    if write:
        json.dump(data, open(PENDING, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('Записано: заметка события дописана.')
    else:
        print('Сухой прогон (--write, чтобы записать).')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--write', action='store_true')
    main(p.parse_args().write)
