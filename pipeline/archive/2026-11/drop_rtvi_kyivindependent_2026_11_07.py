# -*- coding: utf-8 -*-
"""Снять ссылки на RTVI и Kyiv Independent с карточек (владелец, 7 ноября 2026: «иноагентов
убираем»). Хосты добавлены в source_names.UNDESIRABLE_HOSTS; здесь — settle_sources по
карточкам, где они есть. У каждой такой карточки остаются другие источники (assert).

    python3 pipeline/archive/2026-11/drop_rtvi_kyivindependent_2026_11_07.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import source_names as sn  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def apply(data):
    done = []
    for d in data['deals']:
        bad = [s for f in ('src', 'discovery_src') for s in d.get(f) or []
               if isinstance(s, list) and len(s) > 1 and sn.is_undesirable(s[1])]
        if not bad:
            continue
        sn.settle_sources(d)
        assert [s for s in d.get('src') or [] if isinstance(s, list) and len(s) > 1 and str(s[1]).startswith('http')], d['id']
        done.append((d['id'], [s[1][:60] for s in bad]))
    return done


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    for cid, urls in apply(data):
        print('  %s: снято %s' % (cid, urls))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    data = json.load(open(DATA, encoding='utf-8'))
    apply(data)
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv[1:]))
