# -*- coding: utf-8 -*-
"""Второе чтение карточки gd1bf6d5e (Леван Назаров / ЦИАН), 26 ноября 2026:
статус и заголовок спорили с остальными полями той же карточки
(docs/card_acceptance.md, «coherent»/«modality»).

Источник (Коммерсантъ, doc/9130659) хеджирует только РАЗМЕР пакета и личности
продавцов («может консолидировать ОКОЛО 20%», «может составить около 20%» —
«точный размер пакета и детали о продавцах не известны»), но сам факт
покупки источник подает как состоявшийся и подтвержденный покупателем:
«Крупный пакет акций ЦИАН КОНСОЛИДИРОВАЛ инвестор и предприниматель Леван
Назаров» (прошедшее время, без оговорки) и «Леван Назаров ПОДТВЕРДИЛ "Ъ"
ФАКТ ПРИОБРЕТЕНИЯ пакета акций ЦИАН» — это прямое подтверждение самим
покупателем, а не слух. `eco.share`/`law.struct`/`eco.rationale` карточки
уже были написаны в этой, подтвержденной, модальности («купленных через
брокерские группы», прямая цитата Назарова о себе как инвесторе) — а
`status`/`title` из-за ограничений словаря review.STATUS_WORDS (ни «купил»,
ни «приобрел» не лежат дословно в цитате — там «консолидировал»/
«приобретения») остались на «Обсуждается» / «может купить», что стало
спорить с остальными полями той же карточки.

Правится это, не `review.py` (словарь статуса не совпадает буквально с
формой слова в цитате — ровно та же ситуация, что в
pipeline/archive/2026-07/fix_rnl_leasing_avtovaz_deal_fell_through.py),
а прямым скриптом с `assert`: статус на «Закрыта» (независимые признаки
однозначны — docs/card_status_dates.md, «Закрыта — и без слова „закрыла“»:
прошедшее время констатации + подтверждение покупателя), заголовок —
по стандарту CLOSED M&A («X купил [N%] Y», pipeline/title_standard.py).

Запуск:
    python3 pipeline/fix_gd1bf6d5e_status_closed_2026_11_26.py            # сухой прогон
    python3 pipeline/fix_gd1bf6d5e_status_closed_2026_11_26.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PENDING = os.path.join(ROOT, '..', 'static', 'data', 'pending.json')

CARD_ID = 'gd1bf6d5e'
OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Закрыта'
OLD_TITLE = 'Леван Назаров может купить около 20% акций ЦИАН'
NEW_TITLE = 'Леван Назаров купил около 20% акций ЦИАН'


def _get(pending):
    by_id = {c['id']: c for c in pending['cards']}
    assert CARD_ID in by_id, 'карточка %s не нашлась в pending.json' % CARD_ID
    return by_id[CARD_ID]


def main(write):
    pending = json.load(open(PENDING, encoding='utf-8'))
    card = _get(pending)
    assert card.get('status') == OLD_STATUS, 'status уже другой: %r' % card.get('status')
    assert card.get('title') == OLD_TITLE, 'title уже другой: %r' % card.get('title')

    print('Карточка: %s' % CARD_ID)
    print('  status -> %s' % NEW_STATUS)
    print('  title  -> %s' % NEW_TITLE)

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    pending = json.load(open(PENDING, encoding='utf-8'))  # перечитать прямо перед записью
    card = _get(pending)
    assert card.get('status') == OLD_STATUS, 'status изменился параллельно'
    assert card.get('title') == OLD_TITLE, 'title изменился параллельно'
    card['status'] = NEW_STATUS
    card['title'] = NEW_TITLE
    pending['cards'] = [card if c['id'] == CARD_ID else c for c in pending['cards']]
    json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО: status и title обновлены в pending.json')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
