# -*- coding: utf-8 -*-
"""Вычитка 12 ноября 2026, партия m214: то, чего не умеет review.py.

gb1cacbc1 (IPO «Группы Астра»): в eco.finadv стояла фраза статьи с биржевыми тикерами — она уходила в пост
  строкой «Консультанты: …, Организаторами IPO выступили…». Значение переписано списком «фирма — роль»
  (review.py требует, чтобы значение дословно лежало в цитате). Коммерсантъ, 13 октября 2023 года:
  «Организаторами IPO выступили «Старт Капитал», Сбербанк (MOEX: SBER) и Тинькофф-банк (MOEX: TCSG)».

    python3 pipeline/archive/2026-11/reread_oneoff_m214.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY, DAY = 'reread_oneoff_m214', '2026-11-12'
FINADV = {
    'gb1cacbc1': ('Организаторами IPO выступили «Старт Капитал», Сбербанк (MOEX: SBER) и Тинькофф-банк (MOEX: TCSG).',
                  '«Старт Капитал» — организатор IPO; Сбербанк — организатор IPO; Тинькофф Банк — организатор IPO',
                  'Организаторами IPO выступили «Старт Капитал», Сбербанк (MOEX: SBER ) и Тинькофф-банк (MOEX: TCSG ).',
                  'https://www.kommersant.ru/doc/6268920'),
}


def apply(data):
    by = {d['id']: d for d in data['deals']}
    n = 0
    for cid, (old, new, quote, url) in FINADV.items():
        c = by[cid]
        if c['eco'].get('finadv') == new:
            continue
        assert c['eco'].get('finadv') == old, (cid, c['eco'].get('finadv'))
        c['eco']['finadv'] = new
        fact_edit_guard.log(c, 'eco.finadv', new, quote, url, BY, DAY)
        n += 1
    return n


def main(write):
    raw = open(DATA, encoding='utf-8').read()
    old, data = json.loads(raw), json.loads(raw)
    n = apply(data)
    if not n:
        print('Уже применено.')
        return 0
    mass_edit_guard.check(old, data, os.environ.get('MASS_OK'))
    bad = fact_edit_guard.unbacked(old, data)
    assert not bad, bad
    if not write:
        print('Сухой прогон: %d правок. Запись — с ключом --write.' % n)
        return 0
    fresh_raw = open(DATA, encoding='utf-8').read()
    fresh = json.loads(fresh_raw)
    apply(fresh)
    with open(DATA, 'w', encoding='utf-8') as f:
        f.write(json.dumps(fresh, ensure_ascii=False, indent=1) + ('\n' if fresh_raw.endswith('\n') else ''))
    print('ЗАПИСАНО: %d правок.' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
