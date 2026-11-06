# -*- coding: utf-8 -*-
"""Профиль «Центральный городской рынок» (g2f4f1e3e): первое предложение
описания повторяло слово «рынок» из самого имени («Центральный городской
рынок — Городской рынок в Палласовке...») — находка второго чтения карточки
g41bcec82, 6 ноября 2026 (пост читался с тавтологией «рынок — рынок»).
Переписано без повтора слова.

Без ключа — сухой прогон; запись — --write.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CID = 'g2f4f1e3e'
OLD = 'Городской рынок в Палласовке (Волгоградская область): управляет рыночным комплексом и землей под ним. Работает в нынешнем виде с 2024 года.'
NEW = 'Управляет рыночным комплексом и землей под ним в Палласовке (Волгоградская область). Работает в нынешнем виде с 2024 года.'


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    comp = data['companies'][CID]
    if comp['desc'] == NEW:
        print('уже применено')
        return 0
    assert comp['desc'] == OLD, comp['desc']
    comp['desc'] = NEW
    print('%s: desc -> %r' % (CID, NEW))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    data = json.load(open(DATA, encoding='utf-8'))
    comp = data['companies'][CID]
    assert comp['desc'] == OLD, comp['desc']
    comp['desc'] = NEW
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
