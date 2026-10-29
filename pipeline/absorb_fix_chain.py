# -*- coding: utf-8 -*-
"""Поле карточки правилось таблицей FIXES несколько раз (приток, потом
приемка или второе чтение): `test_no_duplicate_fix_for_one_field` допускает
такую цепочку, только если отпечатки всех записей, кроме последней, лежат в
`proofread_absorbed` карточки — так помечается «поле переписано поверх
прежней правки» (docs/card_editing.md). Третий такой случай за два дня
(g0f479af0, g3555ea6e, gfe5d2f94) — вместо одноразового скрипта на каждую
карточку один общий: кладет недостающие отпечатки, текст карточки не меняет.
Карточку ищет и в очереди (`pending.json`), и в базе (`deals_promoted.json`).

Запуск: python3 pipeline/absorb_fix_chain.py <id> <поле> [<поле>…] --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import review  # noqa: E402

PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def _load(path):
    with open(path, encoding='utf-8') as fh:
        raw = fh.read()
    return raw, json.loads(raw)


def _save(path, raw, data):
    out = json.dumps(data, ensure_ascii=False, indent=1)
    if raw.endswith('\n'):
        out += '\n'
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(out)


def main(argv):
    write = '--write' in argv
    args = [a for a in argv if a != '--write']
    assert len(args) >= 2, 'нужны id карточки и хотя бы одно поле'
    card_id, fields = args[0], args[1:]
    raw, data = _load(PENDING)
    cards = data['cards']
    path = PENDING
    card = next((c for c in cards if c['id'] == card_id), None)
    if card is None:
        raw, data = _load(BASE)
        cards, path = data['deals'], BASE
        card = next((c for c in cards if c['id'] == card_id), None)
    assert card is not None, 'карточки %s нет ни в очереди, ни в базе' % card_id
    absorbed = card.setdefault('proofread_absorbed', {})
    added = 0
    for field in fields:
        recs = [f for f in review.FIXES if (f['id'], f['field']) == (card_id, field)]
        assert len(recs) >= 2, 'у %s.%s записей таблицы: %d — цепочки нет' % (card_id, field, len(recs))
        marks = absorbed.setdefault(field, [])
        for f in recs[:-1]:
            fp = review.fix_fingerprint(f['new'])
            if fp not in marks:
                marks.append(fp)
                added += 1
                print('%s.%s: отпечаток %s' % (card_id, field, fp))
    print('добавлено отпечатков: %d (%s)' % (added, os.path.relpath(path, ROOT)))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    if added:
        _save(path, raw, data)
        print('записано')


if __name__ == '__main__':
    main(sys.argv[1:])
