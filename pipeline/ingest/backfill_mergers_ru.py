#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Разовый бэкфил: несколько страниц `mergers.ru/news/` за 8–31 июля разом.

ЗАЧЕМ ОТДЕЛЬНЫЙ СКРИПТ. Обычный `fetch.py` берёт только первую страницу ленты
(самые свежие 30 записей) — этого достаточно для рутины каждые 3 часа, но не
для разового наверстывания периода, за который сайт не обновлялся. У
`mergers.ru/news/` есть постраничная пагинация (`?p=0`, `?p=1`, …), и она уже
устроена как готовая, отфильтрованная под M&A лента — сильно чище, чем общий
поток Коммерсанта/РБК (см. E9: там из 92 «похожих на сделку» реальными
сделками были единицы).

СКОЛЬКО СТРАНИЦ БРАТЬ. По умолчанию 3 (`?p=0..2`) — этого хватает на конец
июня — 31 июля с запасом (замерено: `?p=0` → 31.07–16.07, `?p=1` → 16.07–02.07).
Каждая запись складывается в `data/inbox/raw/<сегодня>.jsonl` — тот же файл и
формат, что и обычный `fetch.py`, поэтому `triage.py`/`match.py`/`draft.py`
дальше работают без изменений.

Запуск:
    python3 pipeline/ingest/backfill_mergers_ru.py            # 3 страницы
    python3 pipeline/ingest/backfill_mergers_ru.py --pages 5  # больше страниц
"""
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fetch  # noqa: E402

SOURCE_ID = 'web:mergers.ru'


def main(pages):
    seen = fetch.seen_urls()
    total, new = 0, []
    for p in range(pages):
        url = 'https://mergers.ru/news/?p=%d' % p if p else 'https://mergers.ru/news/'
        try:
            body = fetch.http_get(url)
        except Exception as e:  # noqa: BLE001
            print('страница %d: ошибка %s' % (p, e))
            continue
        items = fetch.parse_mergers_ru_news(body, SOURCE_ID)
        total += len(items)
        fresh = [it for it in items if it['url'] not in seen]
        for it in fresh:
            seen.add(it['url'])
        new += fresh
        dates = sorted(set(it['published'] for it in items))
        print('страница %d: %d записей (%s — %s), новых %d' % (
            p, len(items), dates[0] if dates else '?', dates[-1] if dates else '?', len(fresh)))

    if not new:
        print('\nНовых записей нет — всё уже было забрано раньше.')
        return

    day = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    path = os.path.join(fetch.RAW, day + '.jsonl')
    os.makedirs(fetch.RAW, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    with open(path, 'a', encoding='utf-8') as f:
        for it in new:
            it['fetched'] = now
            f.write(json.dumps(it, ensure_ascii=False) + '\n')
    print('\nВсего просмотрено: %d, дозаписано новых: %d -> %s' % (total, len(new), path))


if __name__ == '__main__':
    n = 3
    if '--pages' in sys.argv:
        n = int(sys.argv[sys.argv.index('--pages') + 1])
    main(n)
