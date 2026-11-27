# -*- coding: utf-8 -*-
"""Профиль покупателя конюшен в Петергофе (gac82e456): имя «Оз8» без правовой формы, а продавец
в той же карточке gb88e1cdc показан с формой. Форму называет Интерфакс 27 ноября 2026: «По данным
из ЕГРЮЛ, АО "Оз8" было зарегистрировано в Санкт-Петербурге в конце 2024 года». Находка второго
чтения 27 ноября 2026. Профиль заведен сегодня, сделка у него одна; id и адреса не меняются.

Без ключа — сухой прогон; запись — --write.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CID = 'gac82e456'
OLD = '«Оз8»'
NEW = 'АО «Оз8»'


def main(write):
    # файл читается прямо перед записью: чужой пуш не затирается старым снимком
    data = json.load(open(DATA, encoding='utf-8'))
    comp = data['companies'][CID]
    if comp['name'] == NEW:
        print('уже применено')
        return 0
    assert comp['name'] == OLD, comp['name']
    assert comp.get('legal_short') == 'АО «ОЗ8»', comp.get('legal_short')
    comp['name'] = NEW
    print('%s: name %r -> %r' % (CID, OLD, NEW))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
