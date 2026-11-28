# -*- coding: utf-8 -*-
"""Карточка `gd937c845` (OTP Group / российский ОТП Банк): статус возвращается
из «Не состоялась» в «Обсуждается» — решение владельца 28 ноября 2026
(заметка 1855 в ответ на вопрос `gd937c845-status-2026-11-28`: «Давай вернем
статус обсуждается»).

ЧТО В ИСТОЧНИКАХ. 3 ноября Петер Чани сказал, что покупателя не нашли и со
скидкой банк не продадут, — карточку тогда перевели в «Не состоялась». Но в
квартальном отчете 11 ноября группа снова пишет, что пересматривает стратегию
в России, «включая возможность полного ухода», итог — до конца года. Слова
«пока не продаем» сами статус не двигают (docs/card_status_dates.md).

ПОЧЕМУ НЕ ЧЕРЕЗ review.py. Слова источника («приступила к пересмотру
стратегии») нет в `STATUS_WORDS['Обсуждается']`; кроме статуса меняются
элементы списка `events` и `retracted`, чего таблица FIXES не умеет
(docs/card_editing_scripts.md, «Когда review.py не подходит»).

ЧТО МЕНЯЕТСЯ: status, title (глагол по статусу), date (назад к первому
сообщению 28 сентября), событие 3 ноября — из `cancelled` в `negotiations`,
новое событие 11 ноября, `retracted.status` (чтобы enrich.py не вернул срыв
по старой статье), записи `fact_log`. Проза не трогается: `eco.rationale`
уже рассказывает и про слова Чани, и про отчет 11 ноября.

Запуск:
    python3 pipeline/fix_gd937c845_status_back_2026_11_28.py            # сухой прогон
    python3 pipeline/fix_gd937c845_status_back_2026_11_28.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import fact_edit_guard  # noqa: E402

BASE = os.path.join(ROOT, '..', 'static', 'data', 'deals_promoted.json')
CARD_ID = 'gd937c845'
OLD_STATUS, NEW_STATUS = 'Не состоялась', 'Обсуждается'
OLD_TITLE = 'OTP Group отказалась продать российский ОТП Банк'
NEW_TITLE = 'OTP Group рассматривает продажу российского ОТП Банка'
OLD_DATE, NEW_DATE = '2026-11-03', '2026-09-28'
VBR = 'https://www.vbr.ru/novosti/banki/2026/11/12/otp-bank-snova-resil-yiti-iz-rf/'
BLOOMBERG = 'https://www.bloomberg.com/news/articles/2026-09-28/exclusive-hungary-s-otp-bank-looks-at-exiting-russia'
QUOTE = ('OTP Group приступила к пересмотру своей стратегии в отношении российского подразделения, '
         'включая возможность полного ухода из России. Ожидается, что пересмотр стратегии завершится '
         'к концу текущего года')
BY = 'приток 28.11.2026, решение владельца (заметка 1855)'
NEW_EVENT = {
    'kind': 'negotiations',
    'date': '2026-11-11',
    'title': 'OTP Group снова пересматривает стратегию в России',
    'note': ('В квартальном отчете группа написала, что пересматривает стратегию в отношении '
             'российского банка вплоть до полного ухода из России; итог ждет к концу 2026 года.'),
    'source': ['Выберу.ру (12 ноября 2026)', VBR],
}
EVENT_3_NOV_TITLE = 'Покупателя не нашли, со скидкой банк продавать не будут'


def load():
    data = json.load(open(BASE, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    if card is None:
        sys.exit('%s: карточки нет в базе' % CARD_ID)
    return data, card


def check(card):
    assert card.get('status') == OLD_STATUS, 'status изменился: %r' % card.get('status')
    assert card.get('title') == OLD_TITLE, 'title изменился: %r' % card.get('title')
    assert card.get('date') == OLD_DATE, 'date изменилась: %r' % card.get('date')
    ev = card.get('events') or []
    assert len(ev) == 2 and ev[1].get('kind') == 'cancelled' and ev[1].get('date') == '2026-11-03', \
        'events изменились: %r' % [(e.get('kind'), e.get('date')) for e in ev]
    assert ev[0].get('date') == NEW_DATE and ev[0].get('kind') == 'negotiations'


def main(write):
    data, card = load()
    if card.get('status') == NEW_STATUS and card.get('title') == NEW_TITLE:
        print('%s: уже применено' % CARD_ID)
        return 0
    check(card)
    print('%s: status %r -> %r' % (CARD_ID, OLD_STATUS, NEW_STATUS))
    print('%s: title  %r -> %r' % (CARD_ID, OLD_TITLE, NEW_TITLE))
    print('%s: date   %r -> %r' % (CARD_ID, OLD_DATE, NEW_DATE))
    print('%s: событие 3 ноября cancelled -> negotiations (%r)' % (CARD_ID, EVENT_3_NOV_TITLE))
    print('%s: новое событие %s — %s' % (CARD_ID, NEW_EVENT['date'], NEW_EVENT['title']))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0

    data, card = load()                                # перечитать прямо перед записью
    check(card)
    card['status'] = NEW_STATUS
    card['title'] = NEW_TITLE
    card['date'] = NEW_DATE
    ev3 = card['events'][1]
    ev3['kind'] = 'negotiations'
    ev3['title'] = EVENT_3_NOV_TITLE
    card['events'].append(dict(NEW_EVENT))
    retracted = card.setdefault('retracted', {}).setdefault('status', [])
    if OLD_STATUS not in retracted:
        retracted.append(OLD_STATUS)
    fact_edit_guard.log(card, 'status', NEW_STATUS, QUOTE, VBR, BY)
    fact_edit_guard.log(card, 'title', NEW_TITLE, QUOTE, VBR, BY)
    fact_edit_guard.log(card, 'date', NEW_DATE,
                        card['events'][0]['note'], BLOOMBERG, BY)
    json.dump(data, open(BASE, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО: static/data/deals_promoted.json')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
