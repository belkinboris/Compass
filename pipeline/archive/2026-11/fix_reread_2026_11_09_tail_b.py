# -*- coding: utf-8 -*-
"""Вычитка 9 ноября 2026, хвост (б): eco.context g91ec3558 после fix_reread_2026_11_09_tail.py.

text_rules.py --changed поймал «издание в скобках» (source_note): «(в обзоре «Коммерсантъ —
Сделки года» — 172)». Издание называется в тексте отдельной фразой; смысл тот же.

    python3 pipeline/archive/2026-11/fix_reread_2026_11_09_tail_b.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
OLD = ('В сделку вошли 171 магазин — 138 в Москве и 23 в Подмосковье (в обзоре «Коммерсантъ — Сделки года» — 172), '
       'пять производств кулинарии, хлебопекарной и кондитерской продукции и три распределительных центра. ')
NEW = ('В сделку вошли 171 магазин — 138 в Москве и 23 в Подмосковье, пять производств кулинарии, хлебопекарной и '
       'кондитерской продукции и три распределительных центра; в обзоре «Коммерсантъ — Сделки года» магазинов '
       'названо 172. ')


def _apply(data):
    card = next(d for d in data['deals'] if d['id'] == 'g91ec3558')
    ctx = card['eco']['context']
    assert ctx.startswith(OLD), ctx[:200]
    card['eco']['context'] = NEW + ctx[len(OLD):]


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    _apply(data)
    print('g91ec3558 eco.context: издание названо в тексте')
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    fresh = json.load(open(DATA, encoding='utf-8'))
    _apply(fresh)
    json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
