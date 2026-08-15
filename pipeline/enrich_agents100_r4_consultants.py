# -*- coding: utf-8 -*-
"""Консультанты из партии 5 агентов, раунд 4 (15 августа 2026).

Запуск: python3 pipeline/enrich_agents100_r4_consultants.py            # сухой
        python3 pipeline/enrich_agents100_r4_consultants.py --write    # запись
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

PLAN = [
    ('gb21ab6d1',
     'Организатор размещения (IPO)',
     'Финам',
     'Интерфакс: «Организатором размещения является "Финам"» (IPO группы '
     '«Кристалл»). '
     'Источник: https://www.interfax.ru/business/946331',
     'https://www.interfax.ru/business/946331',
     'Стороны сделки',
     ['Стороны сделки']),
    ('g4762fc3d',
     'Консультант DentalPRO',
     'Impactive Capital',
     'Kama Flow в собственном пресс-релизе о раунде DentalPRO: '
     '«Консультантом DentalPRO в сделке выступила компания Impactive '
     'Capital». '
     'Источник: https://www.kamaflow.com/ru/post/dion-soft-developer-'
     'dentalpro-mis-raised-rub-130-million-kama-flow-and-group-co-investors/',
     'https://www.kamaflow.com/ru/post/dion-soft-developer-dentalpro-mis-raised-rub-130-million-kama-flow-and-group-co-investors/',
     'Стороны сделки',
     ['Стороны сделки']),
]

SRC_LABEL = {
    'gb21ab6d1': 'Интерфакс',
    'g4762fc3d': 'Kama Flow',
}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}

    for did, role, firm, note, url, drop, before in PLAN:
        deal = by_id.get(did)
        assert deal is not None, 'карточки %s нет в базе' % did
        adv = (deal.get('law') or {}).get('adv') or []
        names = ' | '.join(str(a[1]) for a in adv if len(a) > 1).lower()
        assert firm.split(' (')[0].lower() not in names, \
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
