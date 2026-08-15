# -*- coding: utf-8 -*-
"""Консультанты из партии 5 агентов, раунд 8 (15 августа 2026).

g14356b25 (CarMoney/АО «СТГ»): law.adv сейчас заглушка, источник называет
организатора размещения — АО ИФК «Солид».
gd75ae46f (ТРЦ «Метрополис»/Balchug Capital): law.adv сейчас заглушка,
источник называет IBC Real Estate консультантом сделки.
gfa0fe27a (Atrium/«Рамо-М»): law.adv уже несёт ALUMNI Partners (консультант
продавца) — CORE.XP упомянут как ВТОРОЙ консультант (представитель
отказался от комментариев, но сам факт участия подтверждён тем же
источником), добавляется, а не заменяет существующую запись.

Запуск: python3 pipeline/enrich_agents100_r8_consultants.py            # сухой
        python3 pipeline/enrich_agents100_r8_consultants.py --write    # запись
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

PLAN = [
    ('g14356b25',
     'Организатор размещения',
     'АО ИФК «Солид»',
     'Организатором размещения выступил АО ИФК «Солид». Источник: '
     'https://vc.ru/u/766795-carmoney/592291-materinskaya-kompaniya-finteh-servisa-carmoney-ao-stg-privlekla-225-mln-rubley-v-akcionernyy-kapital',
     'https://vc.ru/u/766795-carmoney/592291-materinskaya-kompaniya-finteh-servisa-carmoney-ao-stg-privlekla-225-mln-rubley-v-akcionernyy-kapital',
     'Не раскрывались',
     ['Не раскрывались']),
    ('gd75ae46f',
     'Консультант сделки',
     'IBC Real Estate',
     'Эту информацию подтвердили и в консалтинговой компании IBC Real '
     'Estate, которая выступала консультантом этой сделки. Источник: '
     'https://www.vedomosti.ru/realty/articles/2023/04/06/969709-metropolis-smenil-vladeltsa',
     'https://www.vedomosti.ru/realty/articles/2023/04/06/969709-metropolis-smenil-vladeltsa',
     'Не раскрывались',
     ['Не раскрывались']),
    ('gfa0fe27a',
     'Консультант сделки',
     'CORE.XP',
     'Представитель CORE.XP, которая выступает консультантом сделки, от '
     'комментариев отказался. Источник: '
     'https://www.vedomosti.ru/business/articles/2023/04/19/971487-atrium-european-real-estate-zakrila-sdelku-po-prodazhe-rossiiskih-aktivov',
     'https://www.vedomosti.ru/business/articles/2023/04/19/971487-atrium-european-real-estate-zakrila-sdelku-po-prodazhe-rossiiskih-aktivov',
     None,
     ['ALUMNI Partners']),
]

SRC_LABEL = {
    'g14356b25': 'vc.ru',
    'gd75ae46f': 'Ведомости',
    'gfa0fe27a': 'Ведомости',
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
