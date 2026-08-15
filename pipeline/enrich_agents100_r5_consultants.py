# -*- coding: utf-8 -*-
"""Консультанты из партии 5 агентов, раунд 5 (15 августа 2026).

geb343fe1 (ГК «МИЦ») из плана исключён: Forward Legal там уже записан
(та же фирма, та же роль) — находка агента оказалась дублем данных, а не
новым фактом.

Запуск: python3 pipeline/enrich_agents100_r5_consultants.py            # сухой
        python3 pipeline/enrich_agents100_r5_consultants.py --write    # запись
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

PLAN = [
    ('gb1cacbc1',
     'Организаторы IPO',
     '«Старт Капитал», Сбербанк, Тинькофф-банк',
     'Коммерсантъ: «Организаторами IPO выступили "Старт Капитал", '
     'Сбербанк (MOEX: SBER) и Тинькофф-банк (MOEX: TCSG)». '
     'Источник: https://www.kommersant.ru/doc/6268920',
     'https://www.kommersant.ru/doc/6268920',
     None,
     ['Юридический консультант эмитента']),
]

SRC_LABEL = {
    'gb1cacbc1': 'Коммерсантъ',
}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}

    for did, role, firm, note, url, drop, before in PLAN:
        deal = by_id.get(did)
        assert deal is not None, 'карточки %s нет в базе' % did
        adv = (deal.get('law') or {}).get('adv') or []
        names = ' | '.join(str(a[1]) for a in adv if len(a) > 1).lower()
        assert firm.split(',')[0].strip(' «»').lower() not in names, \
            '%s: %s уже записан — перепроверьте' % (did, firm)
        assert [str(a[0]) for a in adv if a] == before, \
            '%s: роли другие (%r), чем ожидалось (%r)' % (
                did, [str(a[0]) for a in adv if a], before)
        if drop:
            assert drop in before, '%s: заглушки «%s» нет' % (did, drop)
        existing_urls = {str(s[1]) for s in (deal.get('src') or []) if len(s) > 1}
        print('%s  %s' % (did, (deal.get('title') or '')[:60]))
        if drop:
            print('    убрать заглушку: %s' % drop)
        print('    + %s — %s' % (role, firm))
        if url in existing_urls:
            print('    (источник уже стоит, src не дублируем)')

    print('\nкарточек к правке: %d' % len(PLAN))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0

    for did, role, firm, note, url, drop, before in PLAN:
        deal = by_id[did]
        law = deal.setdefault('law', {})
        adv = [a for a in (law.get('adv') or []) if not (drop and str(a[0]) == drop)]
        adv.append([role, firm, note])
        law['adv'] = adv
        existing_urls = {str(s[1]) for s in (deal.get('src') or []) if len(s) > 1}
        if url not in existing_urls:
            deal.setdefault('src', []).append([SRC_LABEL[did], url])
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
