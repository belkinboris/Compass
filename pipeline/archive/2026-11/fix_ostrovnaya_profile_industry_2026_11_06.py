# -*- coding: utf-8 -*-
"""Профиль «Птицефабрика «Островная»» (g0a8a70c9), 6 ноября 2026: отрасль
профиля стояла «Пищепром и напитки», как и у самой карточки g8317fa58 до
правки независимого второго чтения. `docs/company_profiles.md`: «Отрасль —
род занятий самой компании» — а род занятий этого профиля (птицеводство,
яичное производство) совпадает с предметом его же единственной сделки.
Все остальные профили-птицефабрики базы несут «Агро», и собственный словарь
отраслей притока (`draft.INDUSTRY_RX`) ловит слово «птицефабрика» как «Агро»
(см. `written_g8317fa58_second_reading_2026_11_06.py`). Оставить профиль с
«Пищепром» при карточке на «Агро» — тот же разъезд, который правило профиля
прямо запрещает.

Запуск: python3 pipeline/archive/2026-11/fix_ostrovnaya_profile_industry_2026_11_06.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
ID = 'g0a8a70c9'


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    comp = data['companies'][ID]
    assert comp['name'] == 'Птицефабрика «Островная»', '%s: не тот профиль' % ID
    assert comp.get('ind') == 'Пищепром и напитки', '%s: ind уже другой (%r)' % (ID, comp.get('ind'))
    comp['ind'] = 'Агро'
    print('%s: ind «Пищепром и напитки» -> «Агро»' % ID)

    if write:
        json.dump(data, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('ЗАПИСАНО')
    else:
        print('сухой прогон — для записи передайте --write')


if __name__ == '__main__':
    main('--write' in sys.argv)
