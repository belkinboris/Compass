# -*- coding: utf-8 -*-
"""Дописать темы карточкам, у которых их не проставил никто, — ничего не удаляя.

ЗАЧЕМ. Темы («Уход иностранного владельца», «Продажа с торгов», «IPO / SPO»)
показываются плашкой на карточке, отдельной подборкой в ленте и графиком на
«Аналитике» — но после промоута их не пересчитывал никто, и у свежих месяцев
поле стояло пустым: замер 3 сентября 2026 — июль 1 карточка из 41, август 0
из 44. Корень починен там, где карточка рождается и дочитывается
(`promote.to_card`, `review.py`), этот скрипт разбирает накопленный хвост.

ПОЧЕМУ НЕ `tag_themes.py --write`. Сплошная перезапись сносит темы, которых
нынешние правила не подтверждают, — таких 82 карточки, их ставили руками и
отдельными скриптами. Здесь только дописывание (`tag_themes.add_themes`):
новая тема появляется, старая не исчезает никогда.

ЧТО БЫЛО ПОЧИНЕНО В САМИХ ПРАВИЛАХ ПЕРЕД ЭТИМ ПРОГОНОМ (иначе хвост принёс
бы в базу шум): «торги» засчитывались и в биржевом смысле («приостановка
торгов на бирже», «30 дней после начала торгов»); «IPO» и «ИИ» ловились в
любом месте текста, даже когда сделка была обычной покупкой доли, а IPO
только упоминалось как чей-то план; «не банкротство» читалось как признак
банкротства. Правила сужены и проверены на себе — см. tag_themes.py.

Запуск:
    python3 pipeline/backfill_themes_add_only.py          # сухой прогон
    python3 pipeline/backfill_themes_add_only.py --write
"""
import collections
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))

import tag_themes  # noqa: E402

PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    before = {d['id']: list(d.get('themes') or []) for d in data['deals']}
    added = collections.Counter()
    touched = []
    for deal in data['deals']:
        new = tag_themes.add_themes(deal)
        if new:
            touched.append((deal['id'], deal.get('title', '')[:70], new))
            for t in new:
                added[t] += 1
    for did, title, new in touched[:20]:
        print('  + %-14s %-70s %s' % (did, title, ', '.join(new)))
    if len(touched) > 20:
        print('  … и ещё %d карточек' % (len(touched) - 20))
    print('\nкарточек затронуто: %d, тем дописано: %d' % (len(touched), sum(added.values())))
    for t, n in added.most_common():
        print('  %4d  %s' % (n, t))

    # Ни одна уже стоявшая тема не должна пропасть — это главная граница
    # скрипта, и она проверяется, а не обещается.
    for deal in data['deals']:
        assert set(before[deal['id']]) <= set(deal.get('themes') or []), \
            'у %s пропала тема' % deal['id']

    with_themes = sum(1 for d in data['deals'] if d.get('themes'))
    print('С темами теперь: %d из %d' % (with_themes, len(data['deals'])))
    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
        print('ЗАПИСАНО в', PATH)


if __name__ == '__main__':
    main(write='--write' in sys.argv)
