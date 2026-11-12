# -*- coding: utf-8 -*-
"""Общая часть разовых скриптов вычитки партии m057 (марафон 12 ноября 2026).

Скрипт партии (`reread_m057_a.py` и следующие) задает списки правок и зовет `run(globals())`:

  NEW_PROFILES — {id: профиль}: новый профиль стороны (id — accept_card._new_profile_id по имени);
  OPS       — {'id', 'field', 'old', 'new', 'quote', 'url'}: поле карточки (через review.get_field/set_field);
              `assert` на старое значение, правка факта — с fact_edit_guard.log (цитата без «ё»);
  PROFILES  — {'pid', 'key', 'old', 'new'}: поле профиля компании, `assert` на старое значение;
  RETRACT   — (id, поле, значение): снятое значение в card['retracted'], чтобы enrich.py его не вернул;
  NOTES     — (id, роль, текст): accepted_notes.no_profile.<роль>;
  ADD_SRC   — {'id', 'src': [подпись, адрес], 'quote', 'first': bool}: источник в src (первым — для первоисточника);
  EVENTS    — {'id', 'date', 'title', 'key', 'old', 'new'}: поле этапа events[] (этап ищется по дате и заголовку);
  REMOVE_SRC — (id, адрес): источник не про эту сделку (доказано чтением) — из src;
  MATCH_KEYS — (id профиля, старые псевдонимы, новые): псевдонимы переименованного профиля;
  GOLD      — (id, ключ, старое, новое): ожидание золотой выборки pipeline/gold/analytics_gold.json, которое
              вычитка исправила вместе с карточкой (запись — только с --write).

Цитата каждой правки должна лежать в тексте, сохраненном save_source.save(..., day='2026-11-12_m057');
проза проходит review.prose_problems. Без ключа — сухой прогон, запись — с --write (базу перечитывает
прямо перед записью; повторный запуск — «уже применено»).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
DAY = '2026-11-12'


def _noyo(s):
    return str(s).replace('ё', 'е').replace('Ё', 'Е')


def apply(g, data, report=None):
    import review
    by = {d['id']: d for d in data['deals']}
    comps = data['companies']
    table = {}
    for fx in review.load_fixes():
        table.setdefault((fx['id'], fx['field']), []).append(fx)
    done = skipped = 0
    for pid, prof in (g.get('NEW_PROFILES') or {}).items():
        if pid in comps:
            skipped += 1
        else:
            comps[pid] = dict(prof)
            done += 1
    for op in g.get('OPS') or []:
        card = by[op['id']]
        cur = review.get_field(card, op['field'])
        if cur == op['new']:
            skipped += 1
            continue
        assert cur == op['old'], (op['id'], op['field'], cur, op['old'])
        review.set_field(card, op['field'], op['new'])
        for fx in table.get((op['id'], op['field']), []):
            if fx.get('new') is not None:
                absorbed = card.setdefault('proofread_absorbed', {}).setdefault(op['field'], [])
                fp = review.fix_fingerprint(fx['new'])
                if fp not in absorbed:
                    absorbed.append(fp)
        if op['field'] in fact_edit_guard.FACT_FIELDS:
            fact_edit_guard.log(card, op['field'], op['new'], _noyo(op['quote']), op['url'], g['BY'], DAY)
        done += 1
    for p in g.get('PROFILES') or []:
        prof = comps[p['pid']]
        if prof.get(p['key']) == p['new']:
            skipped += 1
            continue
        assert prof.get(p['key']) == p['old'], (p['pid'], p['key'], prof.get(p['key']))
        prof[p['key']] = p['new']
        done += 1
    for e in g.get('EVENTS') or []:
        card = by[e['id']]
        ev = [x for x in card.get('events') or [] if x.get('date') == e['date'] and x.get('title') == e['title']]
        assert len(ev) == 1, (e['id'], e['date'], e['title'])
        if ev[0].get(e['key']) == e['new']:
            skipped += 1
            continue
        assert ev[0].get(e['key']) == e['old'], (e['id'], e['key'], ev[0].get(e['key']))
        ev[0][e['key']] = e['new']
        done += 1
    for pid, old, new in g.get('MATCH_KEYS') or []:
        cur = data.setdefault('match_keys', {}).get(pid)
        if cur == new:
            skipped += 1
            continue
        assert cur == old, (pid, cur, old)
        data['match_keys'][pid] = new
        done += 1
    for cid, field, value in g.get('RETRACT') or []:
        lst = by[cid].setdefault('retracted', {}).setdefault(field, [])
        if value not in lst:
            lst.append(value)
    for cid, role, note in g.get('NOTES') or []:
        by[cid].setdefault('accepted_notes', {}).setdefault('no_profile', {})[role] = note
    for s in g.get('ADD_SRC') or []:
        card = by[s['id']]
        src = card.setdefault('src', [])
        have = [x for x in src if x[1] == s['src'][1]]
        if s.get('first'):
            if src and src[0][1] == s['src'][1]:
                continue
            for x in have:
                src.remove(x)
            src.insert(0, list(s['src']))
            done += 1
        elif not have:
            src.append(list(s['src']))
            done += 1
    for cid, url in g.get('REMOVE_SRC') or []:
        card = by[cid]
        if any(x[1] == url for x in card.get('src') or []):
            card['src'] = [x for x in card['src'] if x[1] != url]
            done += 1
    if report is not None:
        report.append((done, skipped))
    return data


def self_check(g):
    """Цитата каждой правки лежит в сохраненном тексте источника; проза проходит правила записи."""
    import review
    big = '\x00'.join(review.flat(x) for x in review.source_texts())

    def real(q):
        parts = [p for p in review.QUOTE_SEP.split(str(q or '')) if p.strip()] or [q]
        return all(review.flat(p) in big for p in parts)
    bad = []
    for op in g.get('OPS') or []:
        if not real(op['quote']):
            bad.append('%s %s: цитаты нет в тексте источника' % (op['id'], op['field']))
        if op['field'] in review.PROSE_WRITTEN and isinstance(op['new'], str) and op['new'] not in ('—', ''):
            for p in review.prose_problems(op['new'], op['quote']):
                bad.append('%s %s: %s' % (op['id'], op['field'], p))
    for s in g.get('ADD_SRC') or []:
        if not real(s['quote']):
            bad.append('%s src: цитаты нет' % s['id'])
    return bad


def run(g):
    write = '--write' in sys.argv[1:]
    raw = open(DATA, encoding='utf-8').read()
    old = json.loads(raw)
    rep = []
    new = apply(g, json.loads(raw), rep)
    print('правок: %d, уже применено: %d' % rep[0])
    if rep[0][0]:
        bad = self_check(g)
        for b in bad:
            print('  ОТКАЗ', b)
        assert not bad, 'есть отказы'
        mass_edit_guard.check(old, new, os.environ.get('MASS_OK'))
        unb = fact_edit_guard.unbacked(old, new)
        assert not unb, unb
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    if not rep[0][0]:
        print('Уже применено.')
        return 0
    gold_path = os.path.join(ROOT, 'pipeline', 'gold', 'analytics_gold.json')
    if g.get('GOLD'):
        graw = open(gold_path, encoding='utf-8').read()
        gold = json.loads(graw)
        rows = gold['deals']
        for cid, key, old_v, new_v in g['GOLD']:
            row = [r for r in rows if r.get('id') == cid]
            assert len(row) == 1, cid
            if row[0].get(key) != new_v:
                assert row[0].get(key) == old_v, (cid, key, row[0].get(key))
                row[0][key] = new_v
        with open(gold_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(gold, ensure_ascii=False, indent=1) + ('\n' if graw.endswith('\n') else ''))
    fresh_raw = open(DATA, encoding='utf-8').read()
    fresh = apply(g, json.loads(fresh_raw))
    with open(DATA, 'w', encoding='utf-8') as f:
        f.write(json.dumps(fresh, ensure_ascii=False, indent=1) + ('\n' if fresh_raw.endswith('\n') else ''))
    print('ЗАПИСАНО.')
    return 0
