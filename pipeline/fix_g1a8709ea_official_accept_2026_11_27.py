# -*- coding: utf-8 -*-
"""Приток 27 ноября 2026, карточка очереди g1a8709ea (основные акционеры «Циана»
продали 52% голосующих акций): правки приемки после официального сообщения
компании, которые не ложатся в FIXES.

- заметка события говорила «сведения неофициальные»; выход трех акционеров
  подтвержден компанией (Интерфакс, 27.11: «Из акционерного капитала МКПАО "Циан"
  полностью вышли структуры Дмитрия Крюкова (32,99%), Дмитрия Демина (7,16%) и
  Максима Мельникова (6,24%)», - сказано в пресс-релизе»). Источник события —
  сообщение компании в пересказе «Интерфакса»;
- прежняя правка строки покупателей (intake_2026_11_27_cian_buyers: «Леван
  Назаров, «Атон», «Д8»») заменена партией intake_2026_11_27_cian_official_accept:
  ее отпечаток уходит в proofread_absorbed, иначе таблица правок считает ее
  неприменной, а поле — правленым дважды.

Дата карточки и события остается годом: «Интерфакс» называет две даты из ленты
раскрытия (18/19 и 26 ноября), главной среди них нет (docs/card_status_dates.md,
«Нет дня — только год»); обе записаны словами в eco.context.

Запуск: python3 pipeline/fix_g1a8709ea_official_accept_2026_11_27.py [--write]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ingest'))
ID = 'g1a8709ea'
NOTE_OLD = ('Компании Дмитрия Крюкова, Дмитрия Демина и Максима Мельникова продали чуть более 52% '
            'голосующих акций; сведения неофициальные.')
NOTE_NEW = ('Компании Дмитрия Крюкова, Дмитрия Демина и Максима Мельникова продали свои акции и '
            'полностью вышли из капитала «Циана». Компания подтвердила это 27 ноября.')
SRC_OLD = ['РБК', 'https://www.rbc.ru/business/27/11/2026/6b0879f6d31da4b02bb5fea9']
SRC_NEW = ['Интерфакс', 'https://www.interfax.ru/business/1131762']
BUYERS_OLD = 'Леван Назаров, «Атон», «Д8»'
BUYERS_NEW = 'Леван Назаров, «Атон»'


def main(write):
    import promote
    import review
    pending = promote.load_pending()
    card = next(c for c in pending['cards'] if c['id'] == ID)
    event = card['events'][0]
    assert event['note'] in (NOTE_OLD, NOTE_NEW), event['note']
    assert event['source'] in (SRC_OLD, SRC_NEW), event['source']
    assert SRC_NEW in card['src'], 'источник события должен стоять в источниках карточки'
    assert card['buyer_name'] == BUYERS_NEW, card['buyer_name']
    event['note'] = NOTE_NEW
    event['source'] = list(SRC_NEW)
    marks = card.setdefault('proofread_absorbed', {}).setdefault('buyer_name', [])
    mark = review.fix_fingerprint(BUYERS_OLD)
    if mark not in marks:
        marks.append(mark)
    print(event['note'])
    print(event['source'])
    print('proofread_absorbed.buyer_name:', marks)
    if write:
        promote.save_pending(pending)
        print('Записано.')
    else:
        print('Сухой прогон. Запись — с ключом --write.')


if __name__ == '__main__':
    main('--write' in sys.argv)
