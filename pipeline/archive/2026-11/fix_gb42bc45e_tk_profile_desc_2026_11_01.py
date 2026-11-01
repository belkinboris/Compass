# -*- coding: utf-8 -*-
"""Профиль g27e4884e (ООО «ТК», калужский франчайзи Rostic’s, карточка gb42bc45e):
описание переписано так, чтобы строка «Предмет» поста читалась одной фразой.

Что было: приемка завела профиль с описанием «Калужский франчайзи Rostic’s: два
ресторана сети, работает с 2014 года. … Юрлицо — ООО «ТК», Калуга.» Пост берет
из описания предмета одно «новое» предложение (`format_post._subject_detail`):
первое совпадало с заголовком по словам и отсеивалось, а заметка о юрлице с
хвостом «, Калуга» не подходила под `_BARE_LEGAL_ENTITY_NOTE` и уходила в пост
— «Предмет: ООО «ТК» (Rostic’s, Калуга) — юрлицо — ООО «ТК», Калуга. …».

Что стало: первое предложение — род занятий своими словами, заметка о юрлице —
голая («Юрлицо — ООО «ТК».»), ее пост отбрасывает сам.

Запуск: python3 pipeline/archive/2026-11/fix_gb42bc45e_tk_profile_desc_2026_11_01.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
CID = 'g27e4884e'
OLD = ('Калужский франчайзи Rostic’s: два ресторана сети, работает с 2014 года. Выручка за 2025 год — '
       '170,6 млн ₽, чистая прибыль — 2 млн ₽. Юрлицо — ООО «ТК», Калуга.')
NEW = ('Оператор двух ресторанов Rostic’s в Калуге, работает с 2014 года. Выручка за 2025 год — '
       '170,6 млн ₽, чистая прибыль — 2 млн ₽. Юрлицо — ООО «ТК».')


def main(argv):
    with open(BASE, encoding='utf-8') as fh:
        raw = fh.read()
    data = json.loads(raw)
    comp = data['companies'][CID]
    assert comp['desc'] == OLD, comp['desc']
    comp['desc'] = NEW
    print('%s: %r -> %r' % (CID, OLD[:40], NEW[:40]))
    if '--write' not in argv:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    out = json.dumps(data, ensure_ascii=False, indent=1)
    if raw.endswith('\n'):
        out += '\n'
    with open(BASE, 'w', encoding='utf-8') as fh:
        fh.write(out)
    print('записано')


if __name__ == '__main__':
    main(sys.argv[1:])
