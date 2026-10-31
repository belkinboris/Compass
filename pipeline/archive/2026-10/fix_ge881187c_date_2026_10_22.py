# -*- coding: utf-8 -*-
"""Карточка ge881187c («Северная верфь»/«Норебо»): дата сделки стояла датой
публикации заметки Ведомостей (22.10.2026), а не датой события — находка
второго чтения. Статья построена на отчетности верфи за первое полугодие
2026 года («следует из данных в отчете… по итогам первого полугодия 2026
г.»): раз продажа уже видна в этой отчетности, сделка закрылась не позже
30 июня 2026 года. Точного дня ни один источник не называет — поэтому дата
в карточке переносится на конец полугодия как крайний известный срок, а
не на день публикации; пояснение — в eco.context (proofread.py).

Без ключа — сухой прогон; запись — --write (файл перечитывается перед записью).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')

OLD_DATE = '2026-10-22'
NEW_DATE = '2026-06-30'


def main():
    write = '--write' in sys.argv
    data = json.load(open(PENDING, encoding='utf-8'))
    card = next(c for c in data['cards'] if c['id'] == 'ge881187c')
    if card.get('date') == NEW_DATE:
        print('ge881187c: дата уже исправлена')
        return 0
    assert card.get('date') == OLD_DATE, card.get('date')
    print('ge881187c: дата %r -> %r' % (card['date'], NEW_DATE))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    data = json.load(open(PENDING, encoding='utf-8'))
    card = next(c for c in data['cards'] if c['id'] == 'ge881187c')
    if card.get('date') == NEW_DATE:
        print('ge881187c: дата уже исправлена (перечитано перед записью)')
        return 0
    assert card.get('date') == OLD_DATE, card.get('date')
    card['date'] = NEW_DATE
    with open(PENDING, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('записано')
    return 0


if __name__ == '__main__':
    sys.exit(main())
