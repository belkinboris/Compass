# -*- coding: utf-8 -*-
"""Приток 27 ноября 2026, карточка gd3822922 («Эфко» купила марку «Моя семья»):
правки по второму чтению, которые не ложатся в FIXES.

- дня сделки источники не называют (сайт «Эфко», «Агроинвестор», «Площадь»):
  дата годом, как у g1a8709ea (docs/card_status_dates.md); 19 ноября — день сообщения;
- law.struct и eco.share очищены: первое говорило, кто сообщил о сделке, а не как
  она устроена, второе слово в слово повторяло предмет;
- extra очищено, заметка события переписана своими словами (приемка).

Запуск: python3 pipeline/fix_gd3822922_second_reading_2026_11_27.py [--write]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ingest'))
ID = 'gd3822922'


def main(write):
    import promote
    pending = promote.load_pending()
    card = next(c for c in pending['cards'] if c['id'] == ID)
    assert card['date'] in ('2026-11-19', '2026'), card['date']
    card['date'] = '2026'
    card.pop('date_basis', None)
    card['events'][0]['date'] = '2026'
    card['law']['struct'] = '—'
    card['eco']['share'] = '—'
    card['extra'] = None
    card['events'][0]['note'] = '«Эфко» сообщила о покупке марки и о том, что уже поставляет продукцию под ней в магазины.'
    print(card['date'], card['law']['struct'], card['eco']['share'])
    if write:
        promote.save_pending(pending)
        print('Записано.')
    else:
        print('Сухой прогон. Запись — с ключом --write.')


if __name__ == '__main__':
    main('--write' in sys.argv)
