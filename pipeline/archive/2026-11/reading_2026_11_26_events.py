"""Вычитка 26 ноября 2026: даты этапов в ленте, которые таблица правок не правит.

- g4afd35d0 (Шереметьево / «Библио-Глобус»): одобрение совета директоров 9 ноября,
  а не 12-го (день заметки Rusbase) — Т—Ж и Interfax, партия month_06.
- ga09376f6 («Экспанта» / «Стаксель»): закрытие 23 октября по истории участников
  ЕГРЮЛ — дата карточки уже 23-е (партия month_05).
- g8a599c40 (Tarkett), gb3837d4d («Менсен»): указ № 738 подписан 15 октября — дата
  карточки уже 15-е (партия month_04).
- g28941fd8 (VEON / Perfectum): этап «закрыта» 27 октября по отчету VEON 6-K и UzDaily
  (статус и дата карточки уже записаны партией month_05); веха ставится
  `review.py --milestone` сразу после.

    python3 pipeline/archive/2026-11/reading_2026_11_26_events.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
SEC = 'https://www.sec.gov/Archives/edgar/data/0001468091/000146809126000046/veonltd6-kq326final.htm'

DATE_FIX = {('g4afd35d0', 'approval'): ('2026-11-12', '2026-11-09'),
            ('ga09376f6', 'closed'): ('2026-10-19', '2026-10-23'),
            ('g8a599c40', 'closed'): ('2026-10-16', '2026-10-15'),
            ('gb3837d4d', 'closed'): ('2026-10-16', '2026-10-15')}


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))   # читается прямо перед записью
    deals = {d['id']: d for d in data['deals']}
    for (did, kind), (old, new) in DATE_FIX.items():
        ev = [e for e in deals[did].get('events') or [] if e.get('kind') == kind]
        assert len(ev) == 1, (did, kind)
        if ev[0]['date'] == new:
            continue
        assert ev[0]['date'] == old, (did, ev[0]['date'])
        ev[0]['date'] = new
        print(did, kind, old, '->', new)
    v = deals['g28941fd8']
    assert v['status'] == 'Закрыта' and v['date'] == '2026-10-27'
    if not any(e.get('kind') == 'closed' for e in v.get('events') or []):
        v.setdefault('events', []).append({
            'kind': 'closed', 'date': '2026-10-27', 'title': 'Сделка завершена',
            'note': 'VEON закрыл покупку Perfectum 27 октября 2026 года; с этой даты оператор входит в отчетность VEON.',
            'source': ['VEON (отчет 6-K, SEC)', SEC]})
        print('g28941fd8 closed 2026-10-27 добавлен')
    if write:
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('записано')


if __name__ == '__main__':
    main('--write' in sys.argv)
