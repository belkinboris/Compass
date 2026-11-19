# -*- coding: utf-8 -*-
"""Применено 19 ноября 2026. gb82efd9f («Медскан»/KDL): строка этапа «Сделка завершена» была дословным куском
анонса РБК с HTML-кодами (&laquo;, &nbsp;) — приемка не ставила штамп. Пересказ своими
словами по тому же предложению пресс-релиза (зеркало РБК, news.mail.ru/society/73165759/):
«Группа компаний «Медскан», входящая в контур управления «Росатома», продала в рамках
сделки «стратегическому партнеру» 49% лабораторного бизнеса «KDL Медскан»».

    python3 pipeline/archive/2026-11/gb82efd9f_event_note_2026_11_19.py [--write]
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
P = os.path.join(ROOT, 'static', 'data', 'pending.json')
OLD = ('Группа компаний &laquo;Медскан&raquo;, входящая в контур управления &laquo;Росатома&raquo;, '
       'продала в рамках сделки стратегическому партнеру 49% лабораторного бизнеса KDL&nbsp;| Медскан.')
NEW = ('Покупатель — стратегический партнер, имя которого «Медскан» не раскрыл; '
       'проданы 49% лабораторного направления KDL, группа из контура «Росатома» сохранила 51%.')

data = json.load(open(P, encoding='utf-8'))
hits = []
def walk(o):
    if isinstance(o, dict):
        if o.get('id') == 'gb82efd9f' and 'events' in o:
            hits.append(o)
        for v in o.values(): walk(v)
    elif isinstance(o, list):
        for v in o: walk(v)
walk(data)
assert len(hits) == 1, len(hits)
ev = hits[0]['events'][0]
assert ev['note'] == OLD, ev['note']
ev['note'] = NEW
print('events[0].note:', NEW)
if '--write' in sys.argv:
    data2 = json.load(open(P, encoding='utf-8'))  # перечитать прямо перед записью
    hits.clear(); walk(data2); assert hits[0]['events'][0]['note'] == OLD
    hits[0]['events'][0]['note'] = NEW
    with open(P, 'w', encoding='utf-8') as f:
        json.dump(data2, f, ensure_ascii=False, indent=1); f.write('\n')
    print('записано')
