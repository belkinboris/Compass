# -*- coding: utf-8 -*-
"""Вычитка 9 ноября 2026 (партии fa–fe): отпечатки всех записей цепочки поля в proofread_absorbed.

Тот же случай, что 3 ноября (absorb_reread_2026_11_03_chains.py): файлы `written_*`
сортируются ПОСЛЕ `reread_2026_11_09_*`, живая запись партии оказывается в середине
цепочки, и `absorb_fix_chain.py` пометил бы ее, оставив старую «последней»
(known_issues/card.md, «absorb_fix_chain.py считает живой последнюю запись по порядку
файлов»). Здесь — по сути: поле уже несет значение одной из записей цепочки (иначе
пропуск); цепочка, которую тест и review.py уже принимают, не трогается; если живая
запись последняя — впитываются прежние, если в середине — все записи цепочки. Затронуты
только карточки партий fa–fe; база перечитывается прямо перед записью.
Запускать после `review.py --write` и apply_reread_oneoff_2026_11_09.py.

    python3 pipeline/archive/2026-11/absorb_reread_2026_11_09_chains.py [--write]
"""
import collections
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import review  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


ONE_OFF_OVERWRITTEN = [('g1d28507c', 'seller'), ('cb7eb501d', 'seller'), ('geb343fe1', 'eco.finadv'),
                       ('citibank', 'eco.context'), ('citibank', 'law.adv')]


def main(write=False):
    raw = open(DATA, encoding='utf-8').read()
    data = json.loads(raw)
    cards = {d['id']: d for d in data['deals']}
    import importlib
    today = set()
    for letter in 'abcde':
        today.update(f['id'] for f in importlib.import_module('fixes.reread_2026_11_09_f' + letter).FIXES)
    chains = collections.defaultdict(list)
    for f in review.FIXES:
        if f['id'] not in today:
            continue
        if f['field'] != 'src':
            chains[(f['id'], f['field'])].append(f)
    added = 0
    for (cid, field), recs in sorted(chains.items()):
        if len(recs) < 2 or cid not in cards:
            continue
        card = cards[cid]
        current = review.get_field(card, field)
        live = [f for f in recs if current == f['new']]
        if not live:
            print('ПРОПУСК %s.%s: ни одна запись не совпадает с полем' % (cid, field))
            continue
        marks = (card.get('proofread_absorbed') or {}).get(field) or []
        head_ok = all(review.fix_fingerprint(f['new']) in marks for f in recs[:-1] if f['new'] is not None)
        if head_ok and review.already_applied(recs[-1], card, data['companies']):
            continue    # цепочка уже в порядке: тест и review.py ее примут
        # Последняя по порядку файлов запись живая — впитываются только прежние;
        # иначе (живая в середине) — все, включая последнюю, уже замененную.
        todo = recs[:-1] if current == recs[-1]['new'] else recs
        marks = card.setdefault('proofread_absorbed', {}).setdefault(field, [])
        for f in todo:
            if f['new'] is None:
                continue
            fp = review.fix_fingerprint(f['new'])
            if fp not in marks:
                marks.append(fp)
                added += 1
                print('%s.%s: %s' % (cid, field, fp))
    # Одиночные прежние записи полей, которые переписал разовый скрипт
    # apply_reread_oneoff_2026_11_09.py (продавец по реестру, консультанты, eco.finadv,
    # проза Ситибанка): запись не применена и не будет — ее отпечаток в proofread_absorbed.
    for cid, field in ONE_OFF_OVERWRITTEN:
        card = cards[cid]
        for f in review.FIXES:
            if (f['id'], f['field']) != (cid, field) or f['new'] is None:
                continue
            if review.already_applied(f, card, data['companies']):
                continue
            marks = card.setdefault('proofread_absorbed', {}).setdefault(field, [])
            fp = review.fix_fingerprint(f['new'])
            if fp not in marks:
                marks.append(fp)
                added += 1
                print('%s.%s: %s (переписано разовым скриптом)' % (cid, field, fp))
    print('добавлено отпечатков: %d' % added)
    if write and added:
        open(DATA, 'w', encoding='utf-8').write(json.dumps(data, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else ''))
        print('записано')


if __name__ == '__main__':
    main('--write' in sys.argv)
