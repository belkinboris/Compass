# -*- coding: utf-8 -*-
"""Приток 22 сентября 2026, карточка g076af76a (Здоровье.ру / Константин
Клюка): привязка предмета к уже существующему профилю компании
g84357246 («Здоровье.ру» — тот же 2023-й раунд Kama Flow, что и в тексте
источника) и починка события, оборванного многоточием на середине слова.
Прямая правка (не через review.py FIXES), тем же способом, каким уже
чинилась привязка seller_id на gffe3c2d0 в этой же сессии: связывание
профиля — внутреннее решение, не факт из источника, ссылка не нуждается
в дословной цитате.

Запуск: python3 pipeline/fix_zdorovie_ru_card_2026_09_22.py --write
"""
import argparse
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')

CARD_ID = 'g076af76a'
TARGET_PROFILE = 'g84357246'

NEW_NOTE = (
    'В ИТ-компании «Здоровье города», которая развивает платформу и приложение '
    '«Здоровье.ру», сменился основной владелец. Бывший ИТ-директор «Альфа групп» и '
    'экс-вице-президент Сбербанка Теймур Штернлиб, бывший топ-менеджер «Крок» Дмитрий '
    'Васильев и структура «Рексофт» избавились от своих долей в компании. 45% получил '
    'бывший владелец гигантского свиноводческого комплекса Константин Клюка.'
)


def main(write):
    data = json.load(open(PENDING, encoding='utf-8'))
    card = next(c for c in data['cards'] if c['id'] == CARD_ID)
    assert card.get('target') is None, 'target уже занят'
    card['target'] = TARGET_PROFILE
    events = card.get('events') or []
    assert events and events[0]['note'].endswith('и…'), 'заметка события уже не та, что ожидали'
    events[0]['note'] = NEW_NOTE
    if write:
        json.dump(data, open(PENDING, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('Записано: target -> %s, заметка события дописана.' % TARGET_PROFILE)
    else:
        print('Сухой прогон (--write, чтобы записать).')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--write', action='store_true')
    main(p.parse_args().write)
