# -*- coding: utf-8 -*-
"""Погасить прежние записи таблицы правок на карточках, поле которых переписала вычитка.

ЗАЧЕМ. 12 ноября 2026, марафон вычитки: партия m006 переписала поля разовым скриптом
(сумма «Не раскрыта», стороны по реестру), а прежние записи таблицы правок на эти поля
остались непогашенными. `review.py` счел их «не примененными», отклонил (старое значение
не совпадает) и по правилу «есть отклоненные — не пишем ничего» остановил запись ВСЕХ
следующих партий. Правило проекта на такой случай есть — отпечаток прежней записи кладется
в `proofread_absorbed` карточки («поле переписано поверх прежней правки»,
docs/card_editing.md), — но делалось это руками. Здесь оно механическое: для выбранных
карточек каждая запись архива и живых партий (кроме партий марафона, которые еще в работе,
и своей), которая не применена, гасится отпечатком. Текст карточки не меняется.

    python3 pipeline/reread_absorb.py --ids g1 g2 … [--skip-tag m017] [--write]
"""
import importlib
import json
import os
import pkgutil
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
os.environ.pop('REVIEW_ONLY', None)
import review  # noqa: E402

BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
IN_WORK = re.compile(r'_m\d{3}(?:\b|_|$)')


def records():
    here = os.path.join(ROOT, 'pipeline', 'ingest')
    out = []
    archive = os.path.join(here, 'fixes_archive')
    for fn in sorted(os.listdir(archive)) if os.path.isdir(archive) else []:
        if fn.endswith('.json'):
            for name, b in json.load(open(os.path.join(archive, fn), encoding='utf-8'))['files'].items():
                out += [(name, f) for f in b['fixes']]
    for mod in sorted(m.name for m in pkgutil.iter_modules([os.path.join(here, 'fixes')])):
        if IN_WORK.search(mod):
            continue                      # партии марафона: свои записи применяются, а не гасятся
        try:
            out += [(mod, f) for f in importlib.import_module('fixes.%s' % mod).FIXES]
        except Exception as e:            # чужой недописанный файл — не наше дело
            print('  пропущен файл правок %s: %s' % (mod, str(e)[:80]))
    return out


def main(argv):
    write = '--write' in argv
    ids = set()
    if '--ids' in argv:
        for a in argv[argv.index('--ids') + 1:]:
            if a.startswith('--'):
                break
            ids.add(a)
    recs = [(n, f) for n, f in records() if f.get('id') in ids]
    data = json.load(open(BASE, encoding='utf-8'))
    comps = data.get('companies')
    by = {d['id']: d for d in data['deals']}
    added = 0
    for name, f in recs:
        card = by.get(f['id'])
        if card is None or f.get('new') is None:
            continue
        try:
            if review.already_applied(f, card, comps):
                continue
        except Exception:
            continue
        new = f['new'][1] if f['field'] == 'src' and isinstance(f['new'], (list, tuple)) and len(f['new']) > 1 else f['new']
        fp = review.fix_fingerprint(new)
        marks = card.setdefault('proofread_absorbed', {}).setdefault(f['field'], [])
        if fp not in marks:
            marks.append(fp)
            added += 1
            print('  погашена %s.%s (%s)' % (f['id'], f['field'], name))
    print('погашено записей: %d' % added)
    if added and write:
        fresh = json.load(open(BASE, encoding='utf-8'))      # перечитать перед записью
        fby = {d['id']: d for d in fresh['deals']}
        for cid in ids:
            if cid in by and cid in fby and by[cid].get('proofread_absorbed'):
                fby[cid]['proofread_absorbed'] = by[cid]['proofread_absorbed']
        json.dump(fresh, open(BASE, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('записано')
    elif added:
        print('Сухой прогон. Запись — с ключом --write.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
