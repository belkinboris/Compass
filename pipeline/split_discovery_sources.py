# -*- coding: utf-8 -*-
"""Источник обнаружения отдельно от источника факта (правило владельца
3 октября 2026, см. `source_names.settle_sources`).

У карточки, где рядом с РБК или Интерфаксом стоит ссылка на @dealsma или
mergers.ru, агрегатор переезжает из `src` (видит читатель) в
`discovery_src` (внутреннее поле). Карточка, у которой агрегатор —
единственный источник, не трогается: её очередь — найти первоисточник
(`--queue` печатает такие карточки, свежие первыми).

Скрипт идемпотентен; тот же перенос делают приток и чтение сами в момент
добавления источника, а инвариант `test_data.py` не даёт хвосту нарасти.

    python3 pipeline/split_discovery_sources.py            # что изменится
    python3 pipeline/split_discovery_sources.py --write
    python3 pipeline/split_discovery_sources.py --queue    # только агрегатор — искать первоисточник
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from pipeline import source_names  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def only_aggregator(card):
    http = source_names._http_sources(card.get('src'))
    return bool(http) and all(source_names.is_aggregator(s[1]) for s in http)


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    if '--queue' in argv:
        rows = [d for d in data['deals'] if only_aggregator(d)]
        rows.sort(key=lambda d: str(d.get('date') or ''), reverse=True)
        print('Карточек, где единственный источник — агрегатор: %d' % len(rows))
        for d in rows:
            print('  %s %s | %s | %s' % (d['id'], d.get('date'), d['title'][:70], d['src'][0][1]))
        return 0
    changed = [d['id'] for d in data['deals'] if source_names.settle_sources(d)]
    print('Агрегатор уходит из видимых источников у %d карточек.' % len(changed))
    if changed[:10]:
        print('  например: %s' % ', '.join(changed[:10]))
    if '--write' in argv and changed:
        with open(DATA, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('Записано.')
    elif changed:
        print('Сухой прогон. Запись — с ключом --write.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
