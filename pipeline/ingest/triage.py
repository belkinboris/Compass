# -*- coding: utf-8 -*-
"""Приток, шаг 2: разобрать сырьё — что это и куда.

ЗАЧЕМ. Между «забрали ленту» и «в базе появилась карточка» есть решение, и оно
должно быть видимым: по каждой записи мы говорим вслух — сделка это или нет, и
если сделка, то новая или уже есть в базе. Результат кладётся в
`data/inbox/triage/<дата>.json` и НЕ трогает основную базу: правки базы —
только через скрипты `pipeline/` с проверками, как и раньше.

ЧЕТЫРЕ ИСХОДА.
  * `not_a_deal` — фильтр `classify.py` сказал «нет»; запись остаётся в сырье,
    и её всегда можно перечитать, если правило окажется слепым.
  * `enrich:<id>` — `match.py` нашёл карточку в базе: это новая новость о
    старой сделке. Такая запись пойдёт в обогащение (и, если факт значимый,
    в правку телеграм-поста).
  * `new` — сделки в базе нет; запись становится черновиком карточки.
  * `duplicate` — этот адрес уже разбирали.

ЧЕГО ЗДЕСЬ НЕТ. Автоматической записи в базу. Карточка собирается из черновика
отдельным шагом с теми же инвариантами, что и весь `pipeline/`: имя стороны
обязано лежать в тексте источника, суммы — в одном формате, роли — по одной на
компанию. Приток без этих проверок наполнил бы базу быстро и неверно.

Запуск:
    python3 pipeline/ingest/triage.py            # разобрать сырьё за сегодня
    python3 pipeline/ingest/triage.py --all      # разобрать всё сырьё
"""
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import classify                                     # noqa: E402
import draft                                        # noqa: E402
import match as matcher                             # noqa: E402

RAW = os.path.join(ROOT, 'data', 'inbox', 'raw')
OUT = os.path.join(ROOT, 'data', 'inbox', 'triage')
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def read_raw(all_days):
    """Файлы ленты за день, БЕЗ кэша полных текстов статей.

    `<дата>-articles.jsonl` пишет `fetch_article_texts.py` — это скачанный
    ПОЛНЫЙ текст уже известного источника, для `review.py`, а не свежая
    новость. Оба файла начинаются с одной и той же даты, и без явного
    исключения `-articles.jsonl` разбор принимал уже привязанный к карточке
    источник за новую запись: `date`/`source_id` у такой записи пустые
    (кэш хранит только `url`/`title`/`summary`), `draft.guess_event()`
    получал `date=None` -> `'unknown'` и час за часом дописывал в ту же
    карточку дублирующий `events[]` с одним и тем же мусорным «unknown»-
    событием, собранным из текста статьи целиком (включая навигацию сайта
    и рекламу) — три раза подряд на `g0ff8c5c4`/`g2c27516d` 1 сентября
    2026, прежде чем найдено здесь.
    """
    day = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    names = sorted(os.listdir(RAW)) if os.path.isdir(RAW) else []
    names = [n for n in names if not n.endswith('-articles.jsonl')]
    if not all_days:
        names = [n for n in names if n.startswith(day)]
    rows = []
    for name in names:
        for line in open(os.path.join(RAW, name), encoding='utf-8'):
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def to_date(published, fallback):
    """Дата публикации в вид YYYY-MM-DD; форматов у лент много, гадать не надо —
    берём то, что распозналось, иначе день забора."""
    text = str(published or '')
    for fmt in ('%a, %d %b %Y %H:%M:%S %z', '%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
        try:
            return datetime.strptime(text.strip(), fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return fallback


def main(argv):
    rows = read_raw('--all' in argv)
    data = json.load(open(DATA, encoding='utf-8'))
    # Один индекс по одному файлу — потому что база теперь одна. До 3 августа
    # 2026 сделки лежали в пяти местах (три массива в index.html, bulk_deals.json
    # и этот файл), приток строил индекс только по последнему и был слеп к 54
    # карточкам: новость о Hugo Boss/«Стокманне» считалась новой сделкой.
    # Слияние убрало не симптом, а саму возможность такой ошибки.
    idx = matcher.index_base(data['deals'], data.get('companies'), data.get('match_keys'))

    result, counts, seen = [], {'not_a_deal': 0, 'enrich': 0, 'new': 0, 'duplicate': 0}, set()
    for row in rows:
        if row['url'] in seen:
            counts['duplicate'] += 1
            continue
        seen.add(row['url'])
        buyer, asset, seller, _ = draft.guess_parties(row.get('title'))
        item = {'title': row.get('title'), 'summary': row.get('summary'), 'url': row.get('url'),
                'date': to_date(row.get('published'), row.get('fetched')),
                'buyer': buyer, 'asset': asset, 'seller': seller}
        if not classify.looks_like_deal(item['title'], row.get('summary', '')):
            counts['not_a_deal'] += 1
            result.append(dict(item, source_id=row.get('source_id'), verdict='not_a_deal'))
            continue
        deal_id, why = matcher.match(item, idx)
        verdict = ('enrich:' + deal_id) if deal_id else 'new'
        counts['enrich' if deal_id else 'new'] += 1
        result.append(dict(item, source_id=row.get('source_id'), verdict=verdict, why=why))

    os.makedirs(OUT, exist_ok=True)
    day = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    path = os.path.join(OUT, day + '.json')
    json.dump({'made': day, 'items': result}, open(path, 'w', encoding='utf-8'),
              indent=1, ensure_ascii=False)

    print('Записей разобрано: %d' % len(rows))
    print('  не сделка:      %d' % counts['not_a_deal'])
    print('  дополнить базу: %d' % counts['enrich'])
    print('  новая сделка:   %d' % counts['new'])
    print('  повтор адреса:  %d' % counts['duplicate'])
    print('Отчёт: %s' % os.path.relpath(path, ROOT))
    for item in result:
        if item['verdict'] != 'not_a_deal':
            print('  [%s] %s' % (item['verdict'], item['title'][:90]))


if __name__ == '__main__':
    main(sys.argv[1:])
