# -*- coding: utf-8 -*-
"""Вычитка 3 ноября 2026 (партии da–dj): отпечатки прежних записей поля в proofread_absorbed.

Запись партии `reread_2026_11_03_*` встает в цепочку правок одного поля, а старые
файлы `written_*` сортируются ПОСЛЕ `reread_*` — `absorb_fix_chain.py` пометил бы
все записи, кроме последней по имени файла, а последней оказывается старая
(known_issues/card.md, «absorb_fix_chain.py считает живой последнюю запись по
порядку файлов»). Здесь — по сути: поле уже несет значение записи этой партии
(иначе пропуск), и отпечатки ВСЕХ записей цепочки, включая живую, кладутся в
proofread_absorbed: тест требует отпечатки всех, кроме последней по порядку файлов,
а живая запись — в середине.
Запускать после `review.py --write`.
"""
import collections
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import review  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def main(write=False):
    raw = open(DATA, encoding='utf-8').read()
    data = json.loads(raw)
    cards = {d['id']: d for d in data['deals']}
    import importlib
    today = set()
    for letter in 'abcdefghij':
        today.update(f['id'] for f in importlib.import_module('fixes.reread_2026_11_03_d' + letter).FIXES)
    chains = collections.defaultdict(list)
    for f in review.FIXES:
        if f['id'] not in today:
            continue
        if f['field'] != 'src':
            chains[(f['id'], f['field'])].append(f)
    added = 0
    for (cid, field), recs in sorted(chains.items()):
        if len(recs) < 2 or cid not in cards:
            continue
        card = cards[cid]
        current = review.get_field(card, field)
        live = [f for f in recs if current == f['new']]
        if not live:
            print('ПРОПУСК %s.%s: ни одна запись не совпадает с полем' % (cid, field))
            continue
        marks = card.setdefault('proofread_absorbed', {}).setdefault(field, [])
        for f in recs:
            if f['new'] is None:
                continue
            fp = review.fix_fingerprint(f['new'])
            if fp not in marks:
                marks.append(fp)
                added += 1
                print('%s.%s: %s' % (cid, field, fp))
    print('добавлено отпечатков: %d' % added)
    if write and added:
        open(DATA, 'w', encoding='utf-8').write(json.dumps(data, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else ''))
        print('записано')


if __name__ == '__main__':
    main('--write' in sys.argv)
