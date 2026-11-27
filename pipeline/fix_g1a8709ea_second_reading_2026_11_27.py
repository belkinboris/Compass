# -*- coding: utf-8 -*-
"""Приток 27 ноября 2026, карточка g1a8709ea (основные акционеры «Циана» продали 52%):
«Предмет / доля» сокращено по второму чтению до одной фразы — первая слово в слово
повторяла предмет сделки, вторая («точный размер — чуть более 52%») спорила сама с собой.
Пустым поле оставлять нельзя: строка «Предмет» в посте берется из него.
Доли продавцов до сделки стоят в контексте.

Запуск: python3 pipeline/fix_g1a8709ea_second_reading_2026_11_27.py [--write]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ingest'))
ID = 'g1a8709ea'
OLD = '52% акций МКПАО «Циан». Точный размер пакета — чуть более 52% голосующих акций.'


def main(write):
    import promote
    pending = promote.load_pending()
    card = next(c for c in pending['cards'] if c['id'] == ID)
    NEW = '52% акций МКПАО «Циан»'  # форма, которую требует приемка: «N% акций АО»
    assert card['eco']['share'] in (OLD, '—', NEW, 'Чуть более 52% голосующих акций МКПАО «Циан»'), card['eco']['share']
    card['eco']['share'] = NEW
    if write:
        promote.save_pending(pending)
        print('Записано.')
    else:
        print('Сухой прогон. Запись — с ключом --write.')


if __name__ == '__main__':
    main('--write' in sys.argv)
