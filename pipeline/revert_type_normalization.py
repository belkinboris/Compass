# -*- coding: utf-8 -*-
"""Откат нормализации типов сделок из fix_proofreading_round2.py.

Нормализация «СП»/«Создание СП»/«Продажа недвижимости» -> «M&A» (5 карточек)
уронила test_curated_feedback_fixes_are_kept: тип «Создание СП» у
selectel-itmo ЗАКРЕПЛЁН тестом как правка из ревью владельца («Правки из
ревью не должны исчезнуть»). Конфликт двух правил — «тип сведён к пяти
значениям» (CLAUDE.md) против прямой кураторской воли — решается не в
пользу моей унификации: раз минимум один тип вне пятёрки поставлен
сознательно и защищён тестом, сводить остальные четыре к M&A тем же жестом
нельзя. Все пять возвращаются к исходным значениям; выбор — узаконить
шестой тип «СП» (со своей плашкой сторон) или свести всё к M&A вместе с
кураторской карточкой — вынесен владельцу (PROOFREADING_CATALOG.md, A8).

Запуск: python3 pipeline/revert_type_normalization.py [--write]
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BACK = [('gmru-geotek-bashneftegeofizika', 'СП'),
        ('gmru-rostech-avia-holding', 'СП'),
        ('selectel-itmo', 'Создание СП'),
        ('gaa603e6d', 'Создание СП'),
        ('agrostroy-zemlya', 'Продажа недвижимости')]

def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    b = {x['id']: x for x in data['deals']}
    for cid, orig in BACK:
        assert b[cid].get('type') == 'M&A', '%s: тип уже не M&A: %r' % (cid, b[cid].get('type'))
        print('%s: type M&A -> %r (возврат)' % (cid, orig))
    if '--write' not in argv:
        print('Сухой прогон. Запись — с ключом --write.'); return 0
    for cid, orig in BACK:
        b[cid]['type'] = orig
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.'); return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
