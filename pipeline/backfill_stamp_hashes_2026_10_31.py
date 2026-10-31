# -*- coding: utf-8 -*-
"""Разовый бэкфилл: отпечатки содержимого к уже стоящим штампам `accepted` и
`second_read` (H4 аудита кода, 31 октября 2026).

С этого дня `accept_card.apply_answer` и `second_reading.apply` пишут рядом со
штампом `accepted_hash` / `second_read_hash` — отпечаток полей, которые читал
принимающий (`readiness.fingerprint`). Разошелся отпечаток у непоказанной
карточки — `readiness.state` = `stale`, и ее берут заново. У штампов, которые
стоят в базе и очереди с прошлых недель, отпечатка нет — такие карточки
несвежими не считаются (иначе все 188 стали бы «stale» разом). Скрипт ставит
отпечатки по сегодняшнему содержимому: с него и начинается отсчет.

Что меняется: только ключи `accepted_hash` и `second_read_hash` у карточек,
у которых есть штамп и нет отпечатка. Состав сделок, профилей, остальные поля
не трогаются. Файлы перечитываются прямо перед записью (рутины пишут те же
файлы каждый час).

Запуск:
    python3 pipeline/backfill_stamp_hashes_2026_10_31.py            # сухой прогон
    python3 pipeline/backfill_stamp_hashes_2026_10_31.py --write    # применить
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import readiness                                              # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
STAMPS = (readiness.ACCEPTED, readiness.SECOND_READ)


def _load():
    base = json.load(open(DATA, encoding='utf-8'))
    pending = json.load(open(PENDING, encoding='utf-8')) if os.path.exists(PENDING) else {'cards': []}
    return base, pending


def stamp_hashes(base, pending):
    """[(где, id, штамп, отпечаток)] — что будет поставлено. Карточка без
    штампа или уже с отпечатком не трогается."""
    comps = base.get('companies') or {}
    plan = []
    for where, cards in (('base', base.get('deals') or []), ('pending', pending.get('cards') or [])):
        for card in cards:
            fp = None
            for stamp in STAMPS:
                if card.get(stamp) and not card.get(stamp + '_hash'):
                    fp = fp or readiness.fingerprint(card, comps)
                    plan.append((where, card['id'], stamp, fp))
    return plan


def main(write=False):
    base, pending = _load()
    plan = stamp_hashes(base, pending)
    by_stamp = {s: sum(1 for p in plan if p[2] == s) for s in STAMPS}
    print('Отпечатков к записи: %d (accepted: %d, second_read: %d; база: %d, очередь: %d)'
          % (len(plan), by_stamp[readiness.ACCEPTED], by_stamp[readiness.SECOND_READ],
             sum(1 for p in plan if p[0] == 'base'), sum(1 for p in plan if p[0] == 'pending')))
    for where, cid, stamp, fp in plan[:8]:
        print('  %-7s %-11s %s_hash = %s' % (where, cid, stamp, fp))
    if len(plan) > 8:
        print('  … и еще %d' % (len(plan) - 8))
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0
    # Перечитываем прямо перед записью: за время прогона рутина могла
    # записать те же файлы; старый снимок молча стер бы ее правки.
    base, pending = _load()
    fresh = stamp_hashes(base, pending)
    comps = base.get('companies') or {}
    by_id = {('base', c['id']): c for c in base.get('deals') or []}
    by_id.update({('pending', c['id']): c for c in pending.get('cards') or []})
    done = 0
    for where, cid, stamp, _fp in fresh:
        card = by_id[(where, cid)]
        assert card.get(stamp) and not card.get(stamp + '_hash'), (where, cid, stamp)
        card[stamp + '_hash'] = readiness.fingerprint(card, comps)
        done += 1
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(base, f, indent=1, ensure_ascii=False)
    if os.path.exists(PENDING):
        with open(PENDING, 'w', encoding='utf-8') as f:
            json.dump(pending, f, indent=1, ensure_ascii=False)
    print('\nЗаписано отпечатков: %d' % done)
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
