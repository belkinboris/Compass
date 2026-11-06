# -*- coding: utf-8 -*-
"""Заголовки вычитанных карточек переписаны по стандарту 6 ноября 2026 поверх прежних правок
заголовка (вычитка, G3). Записи применялись по порядку, каждая к результату предыдущей, поэтому
все, кроме последней, — поглощенные: их отпечатки дописываются в `proofread_absorbed.title`
карточки базы (иначе test_no_duplicate_fix_for_one_field видит две правки на одно поле).

    python3 pipeline/archive/2026-11/fix_absorbed_titles_base_2026_11_06.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import review  # noqa: E402

BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
FILES = ('written_titles_std_a_2026_11_06', 'written_titles_std_b_2026_11_06', 'written_titles_std_c_2026_11_06')


def apply(base):
    ids = set()
    import importlib.util
    for name in FILES:
        spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, 'pipeline', 'ingest', 'fixes', name + '.py'))
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        ids |= {f['id'] for f in m.FIXES}
    cards = {d['id']: d for d in base['deals']}
    added = 0
    for cid in sorted(ids):
        recs = [f for f in review.FIXES if f['id'] == cid and f['field'] == 'title']
        if len(recs) < 2:
            continue
        assert cards[cid]['title'] == recs[-1]['new'], cid
        marks = cards[cid].setdefault('proofread_absorbed', {}).setdefault('title', [])
        for f in recs[:-1]:
            fp = review.fix_fingerprint(f['new'])
            if fp not in marks:
                marks.append(fp)
                added += 1
    return added


def main(argv):
    base = json.load(open(BASE, encoding='utf-8'))
    print('отпечатков: %d' % apply(base))
    if '--write' not in argv:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    base = json.load(open(BASE, encoding='utf-8'))
    apply(base)
    with open(BASE, 'w', encoding='utf-8') as f:
        json.dump(base, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
