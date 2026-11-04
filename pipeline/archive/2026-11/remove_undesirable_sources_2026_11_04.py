"""Снять с карточек ссылки на издания, признанные в РФ нежелательными (4 ноября 2026).

Владелец и Артем: «мы же убирали везде нежелательные в РФ источники» — на
карточках стояли The Insider (12 ссылок) и Meduza (10). Список —
pipeline/source_names.UNDESIRABLE_HOSTS.

    python3 pipeline/archive/2026-11/remove_undesirable_sources_2026_11_04.py          # сухой прогон
    python3 pipeline/archive/2026-11/remove_undesirable_sources_2026_11_04.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)
from pipeline.source_names import is_undesirable  # noqa: E402

PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))      # перечитано прямо перед записью
    touched, removed = [], 0
    for d in data['deals']:
        for field in ('src', 'discovery_src'):
            old = d.get(field) or []
            new = [s for s in old if not (isinstance(s, list) and len(s) > 1 and is_undesirable(s[1]))]
            if len(new) != len(old):
                removed += len(old) - len(new)
                d[field] = new
                touched.append((d['id'], field, len(old), len(new)))
        for fact in (d.get('facts') or {}).values():
            if isinstance(fact, dict) and is_undesirable(fact.get('source') or ''):
                raise SystemExit('факт карточки %s опирается на запрещенный источник — разобрать вручную' % d['id'])
    for t in touched:
        print(*t)
    print('Карточек: %d, ссылок снято: %d' % (len({t[0] for t in touched}), removed))
    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
