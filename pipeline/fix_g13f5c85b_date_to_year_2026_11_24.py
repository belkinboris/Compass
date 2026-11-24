# -*- coding: utf-8 -*-
"""«Рубеж»/Upside Development (g13f5c85b) — переприемка 24 ноября 2026.

Карточка несла `date: "2026-11-06"` при статусе «Закрыта», но этот день ни в
одном источнике не называется как день сделки: все три текста (два материала
«Коммерсанта» и пересказ CRE) датированы 06.11.2026 — это день ПУБЛИКАЦИИ
новости о том, что «Рубеж» «приобрел» офис (Upside Development подтвердила
факт сделки), а не день, когда она закрылась. Ни один текст не называет
месяц или число события словами — только дату выхода материала
(docs/card_status_dates.md, «Дата публикации не уточняет дату сделки»).
День события в реестре/документе не нашелся (сделка купли-продажи
недвижимости, не доли ООО — в ЕГРЮЛ не отражается). Честный вид — дата
годом, подробность (что сделка подтверждена в начале ноября) остается в
`eco.context`/источниках; `date_basis` не нужен (это не уточнение дня, а его
снятие — тот же случай, что «Нет дня — только год», docs/card_status_dates.md).

`review.py` такую правку не принимает (`date_is_supported` требует полный
ГГГГ-ММ-ДД), поэтому — разовый скрипт с `assert` на старое значение.

Запуск: python3 pipeline/fix_g13f5c85b_date_to_year_2026_11_24.py           # проверка
        python3 pipeline/fix_g13f5c85b_date_to_year_2026_11_24.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ROOT)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CID = 'g13f5c85b'
OLD_DATE, NEW_DATE = '2026-11-06', '2026'


def apply(base):
    card = next(c for c in base['deals'] if c['id'] == CID)
    assert card.get('date') == OLD_DATE, 'date изменился: %r' % card.get('date')
    assert card.get('status') == 'Закрыта', 'status изменился: %r' % card.get('status')
    card['date'] = NEW_DATE
    evs = card.get('events') or []
    assert len(evs) == 1 and evs[0].get('kind') == 'closed' and evs[0].get('date') == OLD_DATE, \
        'events изменились: %r' % evs
    evs[0]['date'] = NEW_DATE
    return card


def main(write):
    base = json.load(open(DATA, encoding='utf-8'))
    apply(base)
    print('%s: date %r -> %r (events[0].date тоже)' % (CID, OLD_DATE, NEW_DATE))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    base = json.load(open(DATA, encoding='utf-8'))  # перечитать перед записью
    apply(base)
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(base, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main('--write' in sys.argv))
