# -*- coding: utf-8 -*-
"""Карточка g2dce9ce0 (ВТБ продал агрохолдинг «Лабинский»): events[0].note
собрался автоматически из RSS-сводки Frank Media и попал на экран (карточка
сделки, вкладка «Ход сделки», `e.note` рендерится напрямую, HTML-экранирование
не раскодирует сущности) с необработанными HTML-сущностями `&#171;`/`&#187;`
вместо «»/ и с пресс-штампом «появилось сначала на Frank Media» — то, что
WRITING_BRIEF.md явно запрещает (пересказ прессы). Правка — то же содержание,
дословно декодированное и без штампа.

Запуск:
    python3 pipeline/fix_event_note_g2dce9ce0_2026_10_20.py            # сухой прогон
    python3 pipeline/fix_event_note_g2dce9ce0_2026_10_20.py --write    # применить
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ROOT)
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')

CARD_ID = 'g2dce9ce0'
OLD_NOTE = ('Покупателем стали структуры агрохолдинга &#171;Просторы&#187; Сообщение '
            'ВТБ продал агрохолдинг «Лабинский» за 50 млрд рублей появилось сначала на '
            'Frank Media .')
NEW_NOTE = 'ВТБ объявил, что продал агрохолдинг «Лабинский» за 50 млрд рублей; покупателем стали структуры агрохолдинга «Просторы».'


def main(write=False):
    data = json.load(open(PENDING, encoding='utf-8'))
    card = next((c for c in data['cards'] if c['id'] == CARD_ID), None)
    if not card:
        print('НЕ ТРОГАЕМ %s — карточки нет в очереди' % CARD_ID)
        return 1
    events = card.get('events') or []
    if not events or events[0].get('note') != OLD_NOTE:
        print('НЕ ТРОГАЕМ %s — events[0].note уже другой: %r' % (CARD_ID, events[0].get('note') if events else None))
        return 1
    print('ПРАВИМ %s events[0].note' % CARD_ID)
    print('  было:', OLD_NOTE)
    print('  будет:', NEW_NOTE)
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0
    events[0]['note'] = NEW_NOTE
    json.dump(data, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
