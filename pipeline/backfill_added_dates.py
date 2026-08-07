# -*- coding: utf-8 -*-
"""Проставить `added` — дату, когда карточка появилась в базе.

ЗАЧЕМ. Лента сортируется по дате СДЕЛКИ, и это правильно: читателю нужен
рынок, а не наш график работы. Но из-за этого пополнение не видно. Владелец
7 августа: «не вижу новых карточек с 5 августа» — а карточки были, просто
одобренная вчера сделка от 28 июля встала в середину ленты, между теми, что
лежали там неделю. Отличить свежее от старожила было нечем: даты появления
в данных не было вовсе.

ОТКУДА БЕРЁМ ДАТУ ДЛЯ УЖЕ ЛЕЖАЩИХ КАРТОЧЕК. Из истории git: файл базы
коммитится каждым прогоном, и первый коммит, в котором id встречается, — это
и есть день появления карточки на сайте. Не оценка и не догадка — проверяемый
факт из журнала репозитория.

Дальше поле проставляет `approve.py` при переносе карточки из очереди
модерации в базу, поэтому скрипт разовый.

Запуск:
    python3 pipeline/backfill_added_dates.py            # сухой прогон
    python3 pipeline/backfill_added_dates.py --write    # записать
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
REL = 'static/data/deals_promoted.json'


def commits():
    """(хеш, дата) по всем коммитам файла базы — от старых к новым."""
    out = subprocess.run(['git', 'log', '--reverse', '--format=%H %ad', '--date=short',
                          '--', REL], capture_output=True, text=True, cwd=ROOT).stdout
    return [line.split() for line in out.strip().split('\n') if line.strip()]


def ids_at(commit):
    blob = subprocess.run(['git', 'show', '%s:%s' % (commit, REL)],
                          capture_output=True, text=True, cwd=ROOT).stdout
    if not blob.strip():
        return set()
    try:
        return {d['id'] for d in json.loads(blob).get('deals', [])}
    except ValueError:
        return set()


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    known = {d['id'] for d in data['deals']}
    first_seen, seen = {}, set()
    history = commits()
    print('Коммитов базы в истории: %d — идём от самого старого.' % len(history))
    for i, (sha, day) in enumerate(history):
        present = ids_at(sha)
        for did in present - seen:
            if did in known:
                first_seen[did] = day
        seen |= present
        if i % 25 == 0:
            print('  ...%d/%d (%s), опознано %d' % (i + 1, len(history), day, len(first_seen)))

    missing = known - set(first_seen)
    assert not missing, 'не нашли в истории: %s' % sorted(missing)[:5]
    # Самый старый коммит — это импорт всей базы разом; для тех карточек
    # «дата появления» равна дню импорта и новизны не означает. Это не изъян
    # данных, а честное «пришли одной партией».
    oldest = history[0][1]
    bulk = sum(1 for v in first_seen.values() if v == oldest)
    print('\nРазмечено карточек: %d (из них %d приехали первым импортом %s)'
          % (len(first_seen), bulk, oldest))
    by_day = {}
    for v in first_seen.values():
        by_day[v] = by_day.get(v, 0) + 1
    for day in sorted(by_day)[-6:]:
        print('  %s: +%d' % (day, by_day[day]))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    for d in data['deals']:
        d['added'] = first_seen[d['id']]
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
