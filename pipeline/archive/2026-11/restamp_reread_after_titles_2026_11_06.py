# -*- coding: utf-8 -*-
"""Отметка вычитки после разовой правки заголовков (6 ноября 2026).

136 вычитанных карточек получили заголовок по стандарту (fixes/written_titles_std_[abc]_2026_11_06.py,
с цитатами, review.py). Отпечаток содержимого включает заголовок, и без этого скрипта все 136 встали бы
первыми в очередь повторной вычитки — двойная работа, против которой владелец и просил («Нам двойная
работа не нужна»). Отпечаток `reread_hash` обновляется только у карточек, где по сравнению с HEAD
изменился ТОЛЬКО заголовок, а отпечаток до правки совпадал с отметкой вычитки.

    python3 pipeline/archive/2026-11/restamp_reread_after_titles_2026_11_06.py [--write]
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import readiness  # noqa: E402

BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def plan():
    old = json.loads(subprocess.run(['git', 'show', 'HEAD:static/data/deals_promoted.json'], cwd=ROOT,
                                    capture_output=True, text=True).stdout)
    new = json.load(open(BASE, encoding='utf-8'))
    od = {d['id']: d for d in old['deals']}
    out = []
    for d in new['deals']:
        o = od.get(d['id'])
        if not o or o == d or not d.get('reread'):
            continue
        diff = {k for k in set(o) | set(d) if o.get(k) != d.get(k)}
        if diff - {'title', 'facts', 'proofread_absorbed', 'reviewed'}:
            continue
        if o.get('reread_hash') != readiness.fingerprint(o, old['companies']):
            continue
        out.append(d['id'])
    return new, out


def main(argv):
    new, ids = plan()
    print('отметок к обновлению: %d' % len(ids))
    if '--write' not in argv:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    comps = new['companies']
    for d in new['deals']:
        if d['id'] in ids:
            d['reread_hash'] = readiness.fingerprint(d, comps)
    with open(BASE, 'w', encoding='utf-8') as f:
        json.dump(new, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
