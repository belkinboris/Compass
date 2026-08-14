# -*- coding: utf-8 -*-
"""Консультант из партии 5 агентов, раунд 2 (14 августа 2026) — один случай.

Остальные 6 найденных агентами консультантов (t.me/LawFirms посты 9639-9767)
УЖЕ записаны в базе более ранним проходом по каналу @LawFirms — агенты
нашли их заново через WebSearch, не зная, что они уже на карточке; проверено
прямым чтением `law.adv` каждой карточки перед записью, ничего не дублируется.

gdab53817 (раунд ИнвойсКафе, 150 млн ₽): BITL названа организатором раунда
— поле стояло заглушкой «Стороны сделки» / «Не раскрывались».

Запуск: python3 pipeline/enrich_agents100_r2_consultants.py            # сухой
        python3 pipeline/enrich_agents100_r2_consultants.py --write    # запись
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

PLAN = [
    ('gdab53817',
     'Организатор раунда',
     'BITL',
     'Inc. Russia со ссылкой на компанию: «Согласно оценкам компании BITL, '
     'выступающей организатором текущего раунда, предынвестиционная '
     'стоимость бизнеса составляет 760 млн руб.» '
     'Источник: https://incrussia.ru/news/finteh-platforma-invojskafe-'
     'obyavila-o-privlechenii-investitsij/',
     'https://incrussia.ru/news/finteh-platforma-invojskafe-obyavila-o-privlechenii-investitsij/',
     'Стороны сделки',
     ['Стороны сделки']),
]

SRC_LABEL = {
    'gdab53817': 'Inc. Russia',
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
