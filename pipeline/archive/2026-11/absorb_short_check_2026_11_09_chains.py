# -*- coding: utf-8 -*-
"""Короткая проверка 9 ноября 2026 (партии sa–sj): отпечатки записей цепочки поля в proofread_absorbed.

Тот же случай, что в absorb_reread_2026_11_09_chains.py: у части полей уже была запись
FIXES другой партии (`written_*`, `structural/*`), и запись короткой проверки стала второй
на то же поле; у других полей значение поставил разовый скрипт
apply_short_check_oneoff_2026_11_09.py (заголовок, сумма, доля, консультанты, продавец),
и прежняя запись поля не применена и не будет. По docs/card_editing.md («Правка поля мимо
таблицы синхронизирует запись») прежние записи получают отпечаток `new` в
proofread_absorbed карточки.

Здесь — по сути, а не по порядку файлов: поле уже несет значение одной из записей цепочки
или его поставил разовый скрипт (иначе пропуск с причиной); цепочка, которую тест и
review.py уже принимают, не трогается; если живая запись последняя по порядку — впитываются
прежние, иначе — все записи цепочки. Затронуты только карточки партий sa–sj; база
перечитывается прямо перед записью. Запускать после `review.py --write` и
apply_short_check_oneoff_2026_11_09.py.

    python3 pipeline/archive/2026-11/absorb_short_check_2026_11_09_chains.py [--write]
"""
import collections
import importlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import review  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def _scope():
    """Карточки партий и поля, которые поставил разовый скрипт."""
    ids = set()
    for letter in 'abcdefghij':
        m = importlib.import_module('fixes.reread_2026_11_09_s' + letter)
        ids.update(getattr(m, 'CARDS', []))
        ids.update(f['id'] for f in m.FIXES)
        ids.update(o['id'] for o in getattr(m, 'ONE_OFF', []))
    oneoff = importlib.import_module('apply_short_check_oneoff_2026_11_09')
    by_oneoff = {(o['id'], o['field']) for o in oneoff.OPS if o['op'] in ('set', 'set_any', 'replace')}
    # law.adv.0 / law.adv.0.0 — поле таблицы FIXES одно: law.adv
    by_oneoff |= {(i, 'law.adv') for i, f in by_oneoff if f.startswith('law.adv.')}
    return ids, by_oneoff


def main(write=False):
    raw = open(DATA, encoding='utf-8').read()
    data = json.loads(raw)
    cards = {d['id']: d for d in data['deals']}
    ids, by_oneoff = _scope()
    chains = collections.defaultdict(list)
    for f in review.FIXES:
        if f['id'] in ids and f['field'] != 'src':
            chains[(f['id'], f['field'])].append(f)
    added = 0
    for (cid, field), recs in sorted(chains.items()):
        card = cards.get(cid)
        if card is None:
            continue
        marks = (card.get('proofread_absorbed') or {}).get(field) or []
        head_ok = all(review.fix_fingerprint(f['new']) in marks for f in recs[:-1] if f['new'] is not None)
        if head_ok and review.already_applied(recs[-1], card, data['companies']):
            continue    # цепочка в порядке: тест и review.py ее примут
        current = review.get_field(card, field)
        live = [f for f in recs if current == f['new']]
        if not live and (cid, field) not in by_oneoff:
            print('ПРОПУСК %s.%s: поле не совпадает ни с одной записью и не правилось разовым скриптом' % (cid, field))
            continue
        todo = recs[:-1] if (live and current == recs[-1]['new']) else recs
        marks = card.setdefault('proofread_absorbed', {}).setdefault(field, [])
        for f in todo:
            if f['new'] is None:
                continue
            fp = review.fix_fingerprint(f['new'])
            if fp not in marks:
                marks.append(fp)
                added += 1
                print('%s.%s: %s%s' % (cid, field, fp, '' if live else ' (поле поставил разовый скрипт)'))
    print('добавлено отпечатков: %d' % added)
    if write and added:
        fresh_raw = open(DATA, encoding='utf-8').read()
        assert fresh_raw == raw, 'база изменилась во время прогона — перезапустить'
        open(DATA, 'w', encoding='utf-8').write(json.dumps(data, ensure_ascii=False, indent=1)
                                                + ('\n' if raw.endswith('\n') else ''))
        print('записано')


if __name__ == '__main__':
    main('--write' in sys.argv)
