# -*- coding: utf-8 -*-
"""Консультанты из партии 5 параллельных агентов (14 августа 2026) — два
случая, которые `review.py` не берёт (поле `law.adv` им не покрыто), обе
проверены чтением реально скачанного текста источника.

gd6ce73ed («Рубеж»/логопарк «Внуково 2»): Коммерсантъ называет двух
консультантов сделки, но прямо пишет, что стороны на запрос не ответили —
сторона (покупатель/продавец) не уточняется, роль записана как «Консультант
сделки» без привязки, тем же приёмом, что уже применён к g016f1b13/IBC Real
Estate в волне 2 (см. `enrich_consultants_r1_wave2.py`).

g167e415a (IPO «Делимобиль»): смартлаб называет андеррайтеров размещения —
это не M&A-консультанты, а организаторы IPO, роль записана отдельным
ярлыком.

Запуск: python3 pipeline/enrich_agents100_consultants.py            # сухой
        python3 pipeline/enrich_agents100_consultants.py --write    # запись
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

# (id, роль, фирма, пояснение, url, заглушка_или_None, роли_до)
PLAN = [
    ('gd6ce73ed',
     'Консультант сделки',
     'Bright Rich | CORFAC International',
     'Коммерсантъ называет компанию консультантом сделки по покупке '
     '«Рубежом» площадей в логопарке «Внуково 2»; сторона не уточняется — '
     '«Стороны сделки на запрос "Ъ" не ответили». '
     'Источник: https://www.kommersant.ru/doc/7030621',
     'https://www.kommersant.ru/doc/7030621',
     'Стороны сделки',
     ['Стороны сделки']),
    ('gd6ce73ed',
     'Консультант сделки',
     'Ricci | Склады',
     'Второй консультант той же сделки по тому же источнику — Коммерсантъ '
     'называет обе фирмы консультантами без привязки к стороне. '
     'Источник: https://www.kommersant.ru/doc/7030621',
     'https://www.kommersant.ru/doc/7030621',
     None,
     ['Стороны сделки']),
    ('g167e415a',
     'Андеррайтер размещения (IPO)',
     'Газпромбанк',
     'Смартлаб (финансовый словарь) со ссылкой на ленту раскрытия '
     'информации компании называет андеррайтеров IPO «Делимобиля»: '
     '«В качестве андеррайтеров размещения "Делимобиль" привлек '
     'Газпромбанк, БКС и "Синару"». '
     'Источник: https://smart-lab.ru/finansoviy-slovar/IPO-delimobil',
     'https://smart-lab.ru/finansoviy-slovar/IPO-delimobil',
     'Стороны сделки',
     ['Стороны сделки']),
    ('g167e415a',
     'Андеррайтер размещения (IPO)',
     'БКС',
     'Тот же источник, тот же список андеррайтеров.',
     'https://smart-lab.ru/finansoviy-slovar/IPO-delimobil',
     None,
     ['Стороны сделки']),
    ('g167e415a',
     'Андеррайтер размещения (IPO)',
     'Синара',
     'Тот же источник, тот же список андеррайтеров.',
     'https://smart-lab.ru/finansoviy-slovar/IPO-delimobil',
     None,
     ['Стороны сделки']),
]

SRC_LABEL = {
    'gd6ce73ed': 'Коммерсантъ',
    'g167e415a': 'Smart-lab.ru',
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
