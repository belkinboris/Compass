# -*- coding: utf-8 -*-
"""Консультанты из партии 5 агентов, раунд 6 (15 августа 2026).

ALUMNI Partners (cf9e8af73), ККМП (g4dd7a75c), Denuo (g420cae8d) из плана
исключены: все три уже записаны в базе (более ранний прогон уже нашёл те же
объявления @LawFirms/Denuo) — находки этого раунда оказались дублями данных,
а не новыми фактами.

Запуск: python3 pipeline/enrich_agents100_r6_consultants.py            # сухой
        python3 pipeline/enrich_agents100_r6_consultants.py --write    # запись
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

PLAN = [
    ('g5c3eeb06',
     'Юридический консультант покупателя (Штефан Зочлинг)',
     'DLA Piper (Вена)',
     'extrajournal.net: «Das Wiener Büro der internationalen '
     'Wirtschaftskanzlei DLA Piper berät Unternehmer Stephan Zöchling bei '
     'der Übernahme der ehemaligen Sberbank Europe» — руководитель проекта '
     'Christoph Mager, команда: Jasna Zwitter-Tehovnik, Marc Lager. '
     'Источник: https://extrajournal.net/2023/06/22/sberbank-europe-geht-an-stephan-zoechling-mit-dla-piper/',
     'https://extrajournal.net/2023/06/22/sberbank-europe-geht-an-stephan-zoechling-mit-dla-piper/',
     'Стороны сделки',
     ['Стороны сделки']),
    ('g010ece87',
     'Консультанты сделки',
     'Schoenherr (юридический) и KPMG Белград (финансовый)',
     'Коммерсантъ: «Об этом сообщила юридическая фирма Schoenherr, которая '
     'является одним из консультантов сделки»; «В Schoenherr уточнили, что '
     'финансовым консультантом сделки было белградское отделение KPMG». '
     'Источник: https://www.kommersant.ru/doc/5939524',
     'https://www.kommersant.ru/doc/5939524',
     'Стороны сделки',
     ['Стороны сделки']),
]

SRC_LABEL = {
    'g5c3eeb06': 'extrajournal.net',
    'g010ece87': 'Коммерсантъ',
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
