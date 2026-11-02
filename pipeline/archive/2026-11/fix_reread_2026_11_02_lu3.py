# -*- coding: utf-8 -*-
"""Вычитка 2 ноября 2026, партии l–u: отпечатки прежних записей FIXES в proofread_absorbed.

Вычитка переписала поля, у которых уже были записи прежних прогонов (пересказ,
дочитывание, аудит). По docs/card_editing.md новая запись на то же поле законна,
если отпечатки всех прежних `new` лежат в proofread_absorbed карточки — иначе
test_no_duplicate_fix_for_one_field и already_applied() сочтут прежние записи
неприменимыми. Скрипт дописывает отпечатки только карточкам из файлов партий
reread_2026_11_02_{l..u}.py и только там, где последняя запись уже применена.

    python3 pipeline/archive/2026-11/fix_reread_2026_11_02_lu3.py [--write]
"""
import collections
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import review  # noqa: E402

BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def main(argv):
    raw = open(BASE, encoding='utf-8').read()
    data = json.loads(raw)
    D = {d['id']: d for d in data['deals']}
    ours = set()
    for L in 'lmnopqrstu':
        ns = {}
        exec(open(os.path.join(ROOT, 'pipeline', 'ingest', 'fixes', 'reread_2026_11_02_%s.py' % L), encoding='utf-8').read(), ns)
        ours |= {(f['id'], f['field']) for f in ns['FIXES']}
    recs = collections.defaultdict(list)
    for f in review.FIXES:
        if (f['id'], f['field']) in ours:
            recs[(f['id'], f['field'])].append(f)
    n = 0
    for key, lst in sorted(recs.items()):
        if len(lst) < 2 or key[1] == 'src':
            continue
        card = D[key[0]]
        assert review.already_applied(lst[-1], card, data.get('companies')), key
        marks = card.setdefault('proofread_absorbed', {}).setdefault(key[1], [])
        for f in lst[:-1]:
            if f.get('new') is None:
                continue
            fp = review.fix_fingerprint(f['new'])
            if fp not in marks:
                marks.append(fp)
                n += 1
                print(key[0], key[1])
    print('отпечатков дописано: %d' % n)
    if '--write' not in argv:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    assert open(BASE, encoding='utf-8').read() == raw
    open(BASE, 'w', encoding='utf-8').write(json.dumps(data, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else ''))
    print('записано')


if __name__ == '__main__':
    main(sys.argv[1:])
