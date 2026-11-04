"""Правки после пробной партии карточек изъятий (4 ноября 2026).

1. ИНН 7819301797 теперь у профиля «ООО «БСХ Бытовые Приборы»» (g4b995381); прежний профиль-описание
   g71a4b8f6 («российские заводы Bosch…») — лот, ИНН ему не нужен (decision=lot).
2. g1553af5b (ЮГК): в «Согласованиях» должен быть назван орган — суд.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
REG = os.path.join(ROOT, 'pipeline', 'fns_registry.json')


def main(write):
    base = json.load(open(BASE, encoding='utf-8'))
    reg = json.load(open(REG, encoding='utf-8'))
    row = next(r for r in reg if r['company_id'] == 'g71a4b8f6')
    assert row['inn'] in ('7819301797', None), row
    row.update(decision='no_match', inn=None, date='2026-11-04',
               reason='Профиль — описание нескольких заводов Bosch в России, единого ИНН у лота нет (company.lot=true); '
                      'юрлицо ООО «БСХ Бытовые Приборы» (ИНН 7819301797) заведено отдельным профилем g4b995381.')
    pass
    deal = next(d for d in base['deals'] if d['id'] == 'g1553af5b')
    old = 'Решение от 11 июля 2025 года подлежит немедленному исполнению.'
    assert deal['law']['appr'].startswith(old), deal['law']['appr']
    deal['law']['appr'] = deal['law']['appr'].replace(
        old, 'Решение Советского районного суда Челябинска от 11 июля 2025 года подлежит немедленному исполнению.', 1)
    print('ok')
    if write:
        json.dump(base, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        json.dump(reg, open(REG, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
