# -*- coding: utf-8 -*-
"""Проставить каждой сделке базы объект `facts` (facts.py): прочитанные факты
сохраняются или помечаются stale, остальное предлагается правилами.

Запускается в конце каждого прогона, который трогал карточки (приток,
публикация, качество), перед pytest — иначе `test_facts_are_current` в
test_data.py покраснеет: клиент читает только `facts`, и карточка без них
не участвует ни в одном показателе. Идемпотентен.

Запуск:
    python3 pipeline/facts_derive.py           # сухой прогон: сколько изменится
    python3 pipeline/facts_derive.py --write
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import facts  # noqa: E402
from pipeline import fns_registry  # noqa: E402

DATA = ROOT / 'static' / 'data' / 'deals_promoted.json'


def main(write=False):
    base = json.load(open(DATA, encoding='utf-8'))
    ctx = facts.build_ctx(base, fns_registry.REGISTRY)
    before = {d['id']: json.dumps(d.get('facts'), sort_keys=True) for d in base['deals']}
    changed = facts.derive_all(base, ctx)
    bases = Counter()
    admitted = Counter()
    for d in base['deals']:
        f = d['facts']
        for k in ('stake', 'price'):
            bases[(k, f[k]['basis'])] += 1
        for m, ok in f['admitted'].items():
            admitted[m] += bool(ok)
    print(f'Сделок: {len(base["deals"])}, facts изменятся у {changed}.')
    print('Основания: ' + ', '.join(f'{k}/{b} — {n}' for (k, b), n in sorted(bases.items())))
    print('Допущены: ' + ', '.join(f'{m} — {n}' for m, n in admitted.items()))
    stale = [d['id'] for d in base['deals'] if any((d['facts'].get(k) or {}).get('basis') == 'stale' for k in facts.FACT_KEYS)]
    if stale:
        print(f'Ждут повторного чтения (карточка изменилась после чтения): {len(stale)} — {", ".join(stale[:10])}')
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    if changed:
        json.dump(base, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('Записано.')
    else:
        print('Всё уже актуально.')
    _ = before
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
