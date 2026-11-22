"""Вычитка 22 ноября 2026, хвост партий a и b: прежние записи таблицы правок на поля,
которые вычитка переписала заново (law.struct, eco.context, eco.val, extra, law.appr,
title), — их отпечатки в proofread_absorbed, иначе две живые записи одного поля
(docs/card_editing.md, «Правка поля мимо таблицы»). Фактов не меняет.

    python3 pipeline/ingest/fixes/reread_2026_11_22_c.py [--write]
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest')); sys.path.insert(0, ROOT)
FIXES = []   # таблицы правок нет: только отпечатки

IDS = ['gfa0fe27a', 'gdf93c62d', 'g4a53d81b', 'gb42bc45e', 'gf0dca5dd', 'g2d5a0e2a']

def main(write):
    import review
    path = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
    raw = open(path, encoding='utf-8').read()   # перечитано прямо перед записью
    data = json.loads(raw)
    by = {d['id']: d for d in data['deals']}
    n = 0
    for r in review.load_fixes():
        cid = r.get('id')
        if cid not in IDS or r.get('new') is None or r['field'] == 'src':
            continue
        if review.already_applied(r, by[cid], data.get('companies')):
            continue
        marks = by[cid].setdefault('proofread_absorbed', {}).setdefault(r['field'], [])
        fp = review.fix_fingerprint(r['new'])
        if fp not in marks:
            marks.append(fp); n += 1
            print('  %s %s: прежняя запись поглощена вычиткой' % (cid, r['field']))
    # Правовая форма предмета gabdbe320 — по выписке ЕГРЮЛ (ИНН 7843003738, ОГРН 1157847201380):
    # ООО "КОНДИТЕРСКАЯ ФАБРИКА "КРОНШТАДТСКАЯ"; party_legal_names.py пока не видит профиль на сайте.
    kf = data['companies']['gec2d70f3']
    if not kf.get('legal_short'):
        assert kf.get('inn') == '7843003738', kf.get('inn')
        kf['legal_short'] = 'ООО «Кондитерская фабрика «Кронштадтская»»'; n += 1
        print('  gec2d70f3 legal_short: ООО «Кондитерская фабрика «Кронштадтская»»')
    if write and n:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else ''))
        print('ЗАПИСАНО: %d отпечатков' % n)
    else:
        print('%d отпечатков%s' % (n, '' if write else ' (сухой прогон)'))

if __name__ == '__main__':
    main('--write' in sys.argv)
