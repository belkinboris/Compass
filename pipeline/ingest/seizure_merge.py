#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Свод черновиков карточек изъятий / временного управления в базу (4 ноября 2026).

Владелец: таблица изъятых активов — таблица АКТИВОВ, у каждого актива своя
карточка события; объединенные карточки надо разбить. Читатели-агенты пишут
черновики в data/inbox/seizure_cards/draft_<N>.json (см. BRIEF.md там же), этот
скрипт проверяет их приемкой (`accept_card.findings`) и, только по --write, кладет
в `static/data/deals_promoted.json`.

    python3 pipeline/ingest/seizure_merge.py data/inbox/seizure_cards/draft_1.json          # сухой прогон
    python3 pipeline/ingest/seizure_merge.py data/inbox/seizure_cards/draft_1.json --write  # записать

Что делает с каждой карточкой черновика:
  * id — `keep_id` (разбивка: карточка занимает место старой) или новый `g` + sha1(key)[:8];
  * ставит `no_post: true` (исторические карточки в канал не идут), `added` — сегодня,
    `reviewed`/`accepted` — сегодня, только если приемка не нашла претензий;
  * отказывает, если источник — издание из UNDESIRABLE_HOSTS или карточка ссылается на
    несуществующий профиль;
  * базу перечитывает прямо перед записью (чужой пуш не затирается).
"""
import hashlib
import json
import os
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import accept_card  # noqa: E402
from pipeline.source_names import is_undesirable  # noqa: E402

REQUIRED = ('title', 'date', 'type', 'status', 'src', 'eco', 'law', 'themes', 'ind')


def new_id(key, taken):
    h = 'g' + hashlib.sha1(key.encode('utf-8')).hexdigest()[:8]
    while h in taken:
        h = 'g' + hashlib.sha1((h + key).encode('utf-8')).hexdigest()[:8]
    return h


def build(entry, taken, today):
    card = dict(entry['card'])
    keep = entry.get('keep_id')
    card['id'] = keep or card.get('id') or new_id(entry['key'], taken)
    card.setdefault('added', today)
    card['no_post'] = True
    card.pop('post_preview', None)
    return card


def problems(card, base):
    out = []
    for field in REQUIRED:
        if not card.get(field):
            out.append(('missing:' + field, 'нет поля ' + field))
    for _label, url in card.get('src') or []:
        if is_undesirable(url):
            out.append(('undesirable_source', url))
    comps = base.get('companies') or {}
    for role in ('target', 'buyer', 'seller_id', 'asset_id'):
        ref = card.get(role)
        if ref and str(ref).startswith('g') and ref not in comps and not str(ref).endswith('-target'):
            out.append(('bad_ref:' + role, 'профиля %s нет в базе' % ref))
    return out


def main(argv):
    path = next((a for a in argv if a.endswith('.json')), None)
    if not path:
        print(__doc__)
        return 1
    write = '--write' in argv
    draft = json.load(open(path, encoding='utf-8'))
    base = json.load(open(accept_card.DATA, encoding='utf-8'))   # перечитано прямо перед записью
    deals = base['deals']
    by_id = {d['id']: d for d in deals}
    today = date.today().isoformat()
    ready, bad = [], 0
    taken = set(by_id)
    for entry in draft.get('cards') or []:
        card = build(entry, taken, today)
        taken.add(card['id'])
        keep = entry.get('keep_id')
        if keep and keep not in by_id:
            print('!!', entry['key'], 'keep_id', keep, 'нет в базе')
            bad += 1
            continue
        if not keep and card['id'] in by_id:
            print('!!', entry['key'], 'id уже занят', card['id'])
            bad += 1
            continue
        probe = dict(card)
        base_view = {**base, 'deals': [d for d in deals if d['id'] != keep]}
        found = problems(card, base) + [f for f in accept_card.findings(probe, base_view)]
        print('%s %-9s %s | %s' % ('ОШИБКИ' if found else 'ок    ', card['id'], card['title'][:70], entry.get('op')))
        for code, text in found:
            print('      -', code, ':', str(text)[:240])
        if found:
            bad += 1
        else:
            card['reviewed'] = today
            card[accept_card.STAMP] = today
            ready.append((entry, card))
    for item in draft.get('unresolved') or []:
        print('БЕЗ КАРТОЧКИ', item.get('key'), '—', item.get('why'))
    print('Готово к записи: %d, с претензиями: %d' % (len(ready), bad))
    if write and ready:
        for entry, card in ready:
            keep = entry.get('keep_id')
            if keep:
                old = by_id[keep]
                idx = deals.index(old)
                card.setdefault('added', old.get('added'))
                deals[idx] = card
            else:
                deals.append(card)
        with open(accept_card.DATA, 'w', encoding='utf-8') as f:
            json.dump(base, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Записано: %d' % len(ready))
    return 0 if not bad else 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
