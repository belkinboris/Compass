# -*- coding: utf-8 -*-
"""Две карточки раунда 7, у которых извлечённая цитата в law.struct
начинается со строчной буквы — оборвано подлежащее в начале дословного
фрагмента (см. CLAUDE.md, `test_law_values_start_with_a_capital`).
Правится только РЕГИСТР первой буквы, сам текст не меняется.

После записи нужно вручную привести в соответствие `new`/`quote` в
pipeline/ingest/fixes/batch_agents100_r7.py — иначе
test_review_table_is_applied_and_not_pending упадёт: already_applied()
сверяет значение в базе с `new` дословно.

ЗАПУСК:
    python3 pipeline/fix_r7_capitalize_law_fields.py            # сухой прогон
    python3 pipeline/fix_r7_capitalize_law_fields.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

FIXES = [
    ('gb68699cf', 'law', 'struct'),
    ('gabc53206', 'law', 'struct'),
]


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}

    for cid, section, field in FIXES:
        deal = by_id[cid]
        val = deal[section][field]
        assert val and val[0].islower(), '%s.%s.%s уже с заглавной: %r' % (cid, section, field, val)
        new_val = val[0].upper() + val[1:]
        print('ПРАВИМ %s.%s.%s: %r -> %r' % (cid, section, field, val[:40], new_val[:40]))

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    for cid, section, field in FIXES:
        deal = by_id[cid]
        val = deal[section][field]
        deal[section][field] = val[0].upper() + val[1:]
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
