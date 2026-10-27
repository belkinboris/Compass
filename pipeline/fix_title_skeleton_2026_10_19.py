# -*- coding: utf-8 -*-
"""Дословность, 19 октября 2026: два заголовка повторяли построение заголовка
источника почти слово в слово (verbatim_check.py --from-fixes, скелет
предложения с заменой отдельных слов — g162de6fb 100%, g6c1f9d4e 73%).
Заголовок — структурное поле (review.py требует дословного переноса, не
перефразирования), поэтому правится прямым скриптом, не через FIXES.

    python3 pipeline/fix_title_skeleton_2026_10_19.py          # сухой прогон
    python3 pipeline/fix_title_skeleton_2026_10_19.py --write
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

TITLES = {
    # Retailer.ru: «Бренд детской косметики Nomi перешел под контроль «Гельтека»» — 100% скелета.
    'g162de6fb': ('Бренд детской косметики Nomi перешел под контроль «Гельтека»',
                  '«Гельтек» купил бренд детской косметики Nomi'),
    # РИА Недвижимость: «"Ростех" выставил на торги здания института РАН на Варшавском шоссе» — 73% скелета
    # (у карточки подлежащим стоял организатор торгов «РТ-Капитал», а не продавец «Ростех», но порядок и
    # глагол совпадали почти целиком).
    'g6c1f9d4e': ('«РТ-Капитал» выставила на торги комплекс зданий бывшего НИИ радиотехники РАН на '
                  'Варшавском шоссе',
                  'Здания бывшего НИИ радиотехники РАН на Варшавском шоссе выставлены «Ростехом» на аукцион'),
}


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))      # перечитано прямо перед записью
    by_id = {d['id']: d for d in data['deals']}
    for did, (old, new) in TITLES.items():
        d = by_id[did]
        assert d['title'] == old, (did, d['title'])
        d['title'] = new
        print('%s: %s\n        → %s' % (did, old, new))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
