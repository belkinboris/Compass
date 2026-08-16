# -*- coding: utf-8 -*-
"""Разовая правка: прямые кавычки вместо ёлочек у имён сторон (4 карточки).

ЧТО НЕВЕРНО. Владелец заметил на сайте карточку «"Внуково" приобрело 25,01%
в контролирующей "Домодедово" компании» — прямые кавычки вокруг имён вместо
русских « ». Замер по всей базе (title/buyer_name/seller/asset) нашёл ровно
4 карточки с этим дефектом — не системная беда, единичные накладки разбора:

- g94268c8d: title несёт прямые кавычки у «Внуково» и «Домодедово», хотя
  ВНУТРИ той же карточки (eco.share, seller, buyer_name) те же имена уже
  записаны правильно — « ».
- gdfa13cf0: title и party_evidence.buyer[0].value несут прямые кавычки у
  «Галс Девелопмент».
- g41075b4e: buyer_name — 'ООО "ПСК - Новые решения"'.
- c2d0c1dcd: buyer_name — 'ООО "Антресоль"'.

НЕ ТРОГАЕМ вложенные кавычки второго уровня (например, seller у c514e8712 —
'ООО «Концерн "Россиум"»') — это установленная конвенция базы: внешняя «»,
внутренняя "" при вложенном названии, баланс уже верный (см. CLAUDE.md).

Запуск:
    python3 pipeline/fix_straight_quotes_batch1.py            # сухой прогон
    python3 pipeline/fix_straight_quotes_batch1.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ROOT)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

FIXES = [
    dict(id='g94268c8d', field='title',
         old='"Внуково" приобрело 25,01% в контролирующей "Домодедово" компании',
         new='«Внуково» приобрело 25,01% в контролирующей «Домодедово» компании'),
    dict(id='gdfa13cf0', field='title',
         old='"Галс Девелопмент" купил площадку с БЦ на улице Наметкина в Москве',
         new='«Галс Девелопмент» купил площадку с БЦ на улице Наметкина в Москве'),
    dict(id='gdfa13cf0', field='party_evidence.buyer.0.value',
         old='"Галс Девелопмент"',
         new='«Галс Девелопмент»'),
    dict(id='g41075b4e', field='buyer_name',
         old='ООО "ПСК - Новые решения"',
         new='ООО «ПСК - Новые решения»'),
    dict(id='c2d0c1dcd', field='buyer_name',
         old='ООО "Антресоль"',
         new='ООО «Антресоль»'),
]


def get(obj, path):
    for part in path.split('.'):
        obj = obj[int(part)] if isinstance(obj, list) else obj[part]
    return obj


def set_(obj, path, value):
    parts = path.split('.')
    for part in parts[:-1]:
        obj = obj[int(part)] if isinstance(obj, list) else obj[part]
    last = parts[-1]
    if isinstance(obj, list):
        obj[int(last)] = value
    else:
        obj[last] = value


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}

    for fix in FIXES:
        deal = by_id[fix['id']]
        current = get(deal, fix['field'])
        assert current == fix['old'], (
            '%s.%s уже другое: %r' % (fix['id'], fix['field'], current))
        print('%s.%s: %r -> %r' % (fix['id'], fix['field'], fix['old'], fix['new']))

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    for fix in FIXES:
        set_(by_id[fix['id']], fix['field'], fix['new'])

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('ЗАПИСАНО: %d правок.' % len(FIXES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
