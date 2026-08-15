# -*- coding: utf-8 -*-
"""Консультанты из партии 5 агентов, раунд 7 (15 августа 2026).

g64a94e27 (ВымпелКом MBO): финансовый консультант VEON — Aspring Capital —
новое имя, не дублирует уже записанные LEVEL Legal Services/АЛРУД.
c2455b014 (Ghelamco/Дмитровский логопарк): law.adv сейчас пуст, CORE.XP —
консультант продавца.
g6fc4d4ac (FM Logistic/Central Properties): law.adv сейчас заглушка «не
раскрывались», источник прямо называет NF Group консультантом сделки.

Запуск: python3 pipeline/enrich_agents100_r7_consultants.py            # сухой
        python3 pipeline/enrich_agents100_r7_consultants.py --write    # запись
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

PLAN = [
    ('g64a94e27',
     'Финансовый консультант (холдинг VEON)',
     'Aspring Capital',
     'Финансовым консультантом холдинга VEON по сделке выступил '
     'инвестиционный банк Aspring Capital. Источник: '
     'https://beelinenow.ru/articles/pao-vympelkom-obyavlyaet-o-zavershenii-sdelki-po-vykupu-kompanii-u-mezhdunarodnogo-kholdinga-veon/',
     'https://beelinenow.ru/articles/pao-vympelkom-obyavlyaet-o-zavershenii-sdelki-po-vykupu-kompanii-u-mezhdunarodnogo-kholdinga-veon/',
     None,
     ['LEVEL Legal Services', 'АЛРУД', 'ALRUD']),
    ('c2455b014',
     'Консультант продавца',
     'CORE.XP',
     'Консультантом со стороны продавца называли компанию CORE.XP. '
     'Источник: https://cre.ru/news/98081',
     'https://cre.ru/news/98081',
     None,
     []),
    ('g6fc4d4ac',
     'Консультант сделки',
     'NF Group',
     'В Central Properties и NF Group (консультант сделки) от '
     'комментариев отказались. Источник: '
     'https://www.kommersant.ru/doc/6137534',
     'https://www.kommersant.ru/doc/6137534',
     'Не раскрывались',
     ['Не раскрывались']),
]

SRC_LABEL = {
    'g64a94e27': 'beelinenow.ru',
    'c2455b014': 'cre.ru',
    'g6fc4d4ac': 'Коммерсантъ',
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
        firms_before = [str(a[1]) for a in adv if a]
        assert firms_before == before, \
            '%s: фирмы другие (%r), чем ожидалось (%r)' % (did, firms_before, before)
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
        adv = [a for a in (law.get('adv') or []) if not (drop and str(a[1]) == drop)]
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
