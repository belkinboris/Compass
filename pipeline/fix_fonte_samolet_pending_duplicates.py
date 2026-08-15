# -*- coding: utf-8 -*-
"""15 августа 2026, разбор жалобы владельца: карточка Fonte Capital/«Самолет»
дошла до консоли ДВАЖДЫ (g8422d5c1, gb987ae9e — оба черновика из одного и
того же прогона, с одного и того же URL mergers.ru), и оба одобрены Борисом
— хотя сделка уже три дня как живёт в базе под id g0551fc60 (источник —
Коммерсантъ, дата 2026-08-10, полнее: есть продавец и оценка суммы).

Корень найден: match.quoted() узнавала название стороны только в ёлочках
«…», а заголовок mergers.ru использует прямые кавычки "…" — сигнал
«общее название» отключался целиком, и ни против базы, ни ВНУТРИ одной
партии (сравнение между g8422d5c1 и gb987ae9e) дубль не находился. Починено
в match.py (см. соседний коммит) — но g8422d5c1/gb987ae9e уже одобрены и
ждут в pending.json: следующий прогон approve.py --write просто опубликует
оба как НОВЫЕ карточки, раз patch пока не переисполнил ворота задним числом.

ДЕЙСТВИЕ: снять оба черновика из очереди (сделка уже есть, и полнее), а
mergers.ru добавить вторым источником к g0551fc60 — второй источник не
украшение, это независимое подтверждение.

ЗАПУСК:
    python3 pipeline/fix_fonte_samolet_pending_duplicates.py            # сухой прогон
    python3 pipeline/fix_fonte_samolet_pending_duplicates.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')

DUP_IDS = ('g8422d5c1', 'gb987ae9e')
LIVE_ID = 'g0551fc60'
NEW_SRC = ['Mergers.ru',
           'https://mergers.ru/news/Struktura-Fonte-Capital-iz-Kazahstana-priobrela-18-akcij-Samoleta-u-naslednikov-Mihaila-Kenina-87349']


def main(argv):
    pending = json.load(open(PENDING, encoding='utf-8'))
    ids_in_pending = {c['id'] for c in pending['cards']}
    for cid in DUP_IDS:
        assert cid in ids_in_pending, '%s: уже не в очереди — проверьте вручную' % cid

    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    live = by_id[LIVE_ID]
    existing_urls = {str(s[1]) for s in (live.get('src') or []) if len(s) > 1}

    print('СНИМАЕМ из очереди: %s' % ', '.join(DUP_IDS))
    if NEW_SRC[1] not in existing_urls:
        print('ДОБАВЛЯЕМ источник %s -> %s' % (LIVE_ID, NEW_SRC[1]))
    else:
        print('источник %s уже стоит у %s' % (NEW_SRC[1], LIVE_ID))

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    pending['cards'] = [c for c in pending['cards'] if c['id'] not in DUP_IDS]
    json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

    if NEW_SRC[1] not in existing_urls:
        live.setdefault('src', []).append(NEW_SRC)
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
