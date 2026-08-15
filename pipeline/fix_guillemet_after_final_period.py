# -*- coding: utf-8 -*-
"""Откат второй собственной ошибки того же прогона типографики.

`fix_typography_across_base.py` дописывал недостающую закрывающую ёлочку в
КОНЕЦ поля. Для 22 полей это верно — там имя в кавычках и правда стояло
последним. Но у 18 полей перекос возник где-то в середине абзаца, и
дописанная в конец кавычка вставала ПОСЛЕ финальной точки:

    «…выпустила 1,045 млн т продукции в живом весе.»

Это не починка, а перенос поломки в другое место: закрывающая кавычка после
точки читается как обрыв, а настоящее место пропущенного знака — внутри
предложения, и вычислить его механически нельзя. Здесь действует уже
записанное правило CLAUDE.md: «Досочинить обрубленный факт — не вариант» —
дописывать можно ТО, ЧТО ДОКАЗУЕМО, а «кавычка была где-то раньше» не
доказуемо. Возвращаем этим 18 полям исходный перекос: он честнее.

Признак отката — ровно тот, что описан выше: поле отличается от версии в
git HEAD только дописанными в конец «»», и перед ними стоит «.», «!» или «?».

Запуск:
    python3 pipeline/fix_guillemet_after_final_period.py            # сухой прогон
    python3 pipeline/fix_guillemet_after_final_period.py --write    # запись
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

TRAILING = re.compile(r'[.!?]»+$')


def text_fields(deal):
    out = []
    if isinstance(deal.get('extra'), str):
        out.append(('extra', None, deal['extra']))
    for group in ('eco', 'law'):
        for key, value in (deal.get(group) or {}).items():
            if isinstance(value, str):
                out.append((group, key, value))
    return out


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    raw = subprocess.run(['git', 'show', 'HEAD:static/data/deals_promoted.json'],
                         capture_output=True, text=True, cwd=ROOT).stdout
    old = {d['id']: d for d in json.loads(raw)['deals']}

    todo = []
    for cid, deal in by_id.items():
        if cid not in old:
            continue
        was = {(g, k): v for g, k, v in text_fields(old[cid])}
        for group, key, current in text_fields(deal):
            before = was.get((group, key))
            if before is None or current == before:
                continue
            # отличие ровно в дописанных в конец ёлочках, и они после точки
            if current.rstrip('»') == before.rstrip('»') and \
                    len(current) > len(before) and TRAILING.search(current):
                todo.append((cid, group, key, current, before))

    print('Полей, где закрывающая ёлочка встала после финальной точки: %d' % len(todo))
    for cid, group, key, cur, back in todo[:6]:
        name = group if key is None else '%s.%s' % (group, key)
        print('  %s %-16s %r -> %r' % (cid, name, cur[-38:], back[-38:]))

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    for cid, group, key, _cur, back in todo:
        if key is None:
            by_id[cid]['extra'] = back
        else:
            by_id[cid][group][key] = back

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('ЗАПИСАНО: %d полей возвращено к исходному виду.' % len(todo))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
