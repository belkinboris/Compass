# -*- coding: utf-8 -*-
"""Применено 20 ноября 2026. «Медскан»/KDL (gb82efd9f): предмет сделки — профиль
«Медскан Лаб» (g6288a1cc, ООО «Медскан Лаб», ИНН 9717118570, в реестре ФНС с
23 октября 2026), а не текст. Приемка 19 ноября ошибочно записала в
no_profile.target «отдельного профиля в базе нет, заводить не стали» — профиль был.
«Медскан Лаб» — холдинговая компания лабораторного бизнеса группы: в ней Сбербанк
держал 49%, затем 39% (карточки g0410fde2, gc9461b5c), по ней раскрыт опцион
18 ноября. Отчетность — ГИР БО через тот же код, что у приемки (target_financials).
Карточка лежит и в базе (опубликована, пост 293), и в pending.json — правятся обе.

    python3 pipeline/archive/2026-11/gb82efd9f_target_medskan_lab_2026_11_20.py [--write]
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest')); sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import accept_card
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PEND = os.path.join(ROOT, 'static', 'data', 'pending.json')
TID, INN, LEGAL = 'g6288a1cc', '9717118570', 'ООО «Медскан Лаб»'
REASON_OLD = 'заводить профиль ради одной сделки не стали'

def fix(card, comps, fns):
    assert card.get('target') in (None, TID), card.get('target')
    assert TID in comps
    out = []
    card['target'] = TID
    notes = card.setdefault('accepted_notes', {})
    nop = notes.get('no_profile') or {}
    if REASON_OLD in str(nop.get('target') or ''):
        nop.pop('target'); out.append('снята ошибочная причина no_profile.target')
    note = accept_card.target_financials(card, comps, INN, LEGAL, fns)
    out.append(note or 'target_fin уже с числами')
    return out

fns = accept_card.fns_client_or_none()
assert fns is not None, 'нет клиента ФНС'
base = json.load(open(DATA, encoding='utf-8')); pend = json.load(open(PEND, encoding='utf-8'))
for name, obj, cards in (('база', base, base['deals']), ('очередь', pend, pend['cards'])):
    c = [x for x in cards if x['id'] == 'gb82efd9f']
    if c:
        print(name, fix(c[0], base['companies'], fns), '\n  target_fin:', c[0]['eco'].get('target_fin'))
if '--write' in sys.argv:
    for path, obj in ((DATA, base), (PEND, pend)):
        raw = open(path, encoding='utf-8').read()
        out = json.dumps(obj, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else '')
        open(path, 'w', encoding='utf-8').write(out)
    print('записано')
