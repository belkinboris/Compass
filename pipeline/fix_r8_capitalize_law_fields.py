# -*- coding: utf-8 -*-
"""Четыре карточки раунда 8, у которых извлечённая цитата в law.struct/
law.terms начинается со строчной буквы — оборвано начало дословного
фрагмента (см. CLAUDE.md, `test_law_values_start_with_a_capital`). Плюс
buyer_name карточки g88d5e740, попавший в косвенный падеж («Структуры» —
pymorphy разобрал как родительный, тест `test_party_name_is_in_the_nominative_case`
это не пропускает); правится на единственное число «Структура».

Правится только формулировка, не факт. После записи нужно вручную
привести в соответствие `new` в pipeline/ingest/fixes/batch_agents100_r8.py
для четырёх law.*-записей — иначе test_review_table_is_applied_and_not_pending
упадёт (already_applied() сверяет базу с `new` дословно).

ЗАПУСК:
    python3 pipeline/fix_r8_capitalize_law_fields.py            # сухой прогон
    python3 pipeline/fix_r8_capitalize_law_fields.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CAPITALIZE = [
    ('gec8d0f1a', 'law', 'struct'),
    ('gf23149cf', 'law', 'struct'),
    ('ga3ca0cde', 'law', 'terms'),
    ('gbf1e6917', 'law', 'struct'),
]

BUYER_NAME_FIX = ('g88d5e740', 'Структуры Евгения Зубицкого (ПМХ)',
                   'Структура Евгения Зубицкого (ПМХ)')


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}

    for cid, section, field in CAPITALIZE:
        deal = by_id[cid]
        val = deal[section][field]
        assert val and val[0].islower(), '%s.%s.%s уже с заглавной: %r' % (cid, section, field, val)
        new_val = val[0].upper() + val[1:]
        print('ПРАВИМ %s.%s.%s: %r -> %r' % (cid, section, field, val[:40], new_val[:40]))

    cid, old_name, new_name = BUYER_NAME_FIX
    deal = by_id[cid]
    assert deal.get('buyer_name') == old_name, \
        '%s: buyer_name уже другой: %r' % (cid, deal.get('buyer_name'))
    print('ПРАВИМ %s.buyer_name: %r -> %r' % (cid, old_name, new_name))

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    for cid, section, field in CAPITALIZE:
        deal = by_id[cid]
        val = deal[section][field]
        deal[section][field] = val[0].upper() + val[1:]

    by_id[cid := BUYER_NAME_FIX[0]]['buyer_name'] = BUYER_NAME_FIX[2]

    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
