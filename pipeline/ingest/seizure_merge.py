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

REGISTRY_JSON = os.path.join(ROOT, 'pipeline', 'fns_registry.json')
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


def absorb_old_fixes(card, old, keep):
    """Карточка переписана целиком: прежние записи таблицы правок (FIXES) к ней больше не совпадают
    с полями. Как у вычитки, их отпечатки уходят в `proofread_absorbed` — `already_applied` их засчитает."""
    import review
    absorbed = {k: list(v) for k, v in (old.get('proofread_absorbed') or {}).items()}
    for fix in review.FIXES:
        if fix['id'] != keep or fix['new'] is None:
            continue
        value = fix['new'][1] if fix['field'] == 'src' else fix['new']
        fp = review.fix_fingerprint(value)
        if fp not in absorbed.setdefault(fix['field'], []):
            absorbed[fix['field']].append(fp)
    if absorbed:
        card['proofread_absorbed'] = absorbed


def profile_id(key):
    return 'g' + hashlib.sha1(('profile:' + key).encode('utf-8')).hexdigest()[:8]


def apply_profiles(draft, base, registry, today):
    """Новые профили компаний из черновика: {key, name, ind, desc, inn, inn_reason}.
    Профиль + запись реестра ФНС (ИНН подтвержден чтением реестра/rusprofile)."""
    import fns_registry as fr
    made, problems_ = {}, []
    comps = base.setdefault('companies', {})
    for p in draft.get('profiles') or []:
        pid = profile_id(p['key'])
        if not fr.inn_is_valid(str(p.get('inn') or '')):
            problems_.append('профиль %s: ИНН %r не проходит контрольную сумму' % (p['key'], p.get('inn')))
            continue
        for k in ('name', 'ind', 'desc', 'inn_reason'):
            if not p.get(k):
                problems_.append('профиль %s: нет поля %s' % (p['key'], k))
        if pid in comps:
            made[p['key']] = pid
            continue
        comps[pid] = {'name': p['name'], 'ind': p['ind'], 'desc': p['desc'], 'kpi': ['Профиль', 'Автоматический']}
        if not any(r['company_id'] == pid for r in registry):      # повторный свод не дублирует запись
            registry.append({'company_id': pid, 'decision': 'confirmed', 'inn': str(p['inn']),
                             'reason': p['inn_reason'], 'date': today})
        made[p['key']] = pid
    return made, problems_


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
    registry = json.load(open(REGISTRY_JSON, encoding='utf-8'))
    profiles, profile_problems = apply_profiles(draft, base, registry, today)
    for text in profile_problems:
        print('!!', text)
    ready, bad = [], len(profile_problems)
    taken = set(by_id)
    for entry in draft.get('cards') or []:
        card = build(entry, taken, today)
        ref = card.pop('target_profile', None)       # ключ профиля из черновика -> id
        if ref:
            if ref not in profiles:
                print('!!', entry['key'], 'профиль', ref, 'не описан в profiles')
                bad += 1
                continue
            card['target'] = profiles[ref]
            (card.get('accepted_notes') or {}).get('no_profile', {}).pop('target', None)
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
        found = problems(card, base) + [f for f in accept_card.findings(probe, base_view, registry=registry)]
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
                absorb_old_fixes(card, old, keep)
                deals[idx] = card
            else:
                deals.append(card)
        with open(accept_card.DATA, 'w', encoding='utf-8') as f:
            json.dump(base, f, ensure_ascii=False, indent=1)
            f.write('\n')
        with open(REGISTRY_JSON, 'w', encoding='utf-8') as f:
            json.dump(registry, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Записано: %d, профилей: %d' % (len(ready), len(profiles)))
    return 0 if not bad else 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
