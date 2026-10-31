# -*- coding: utf-8 -*-
"""Salmon Group (g32cfa1d4): два механических дефекта, оба проверены заранее
против review.FIXES — записей на эти поля не было.

1. `eco.sum` стоял прочерком, хотя `sum` («Обзор») уже несет сумму раунда —
   восьмой случай пробела `accept_card.py` (`sum_fields_differ` не ловит
   пустой `eco.sum`), записанного в KNOWN_ISSUES.md.
2. `ind` стояло «Финансовые технологии» — синоним, не входящий в список
   `INDUSTRIES` на сайте (там каноническое «Финтех»): пост и фильтр по
   отрасли карточку бы не находили.

Без ключа — сухой прогон, запись по --write.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

OLD_SUM = '—'
NEW_SUM = '$140 млн ($90 млн акции, $50 млн облигации)'
OLD_IND = 'Финансовые технологии'
NEW_IND = 'Финтех'


def main():
    write = '--write' in sys.argv
    data = json.load(open(DATA, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == 'g32cfa1d4')
    assert card['sum'] == NEW_SUM, card['sum']
    assert card['eco']['sum'] == OLD_SUM, card['eco']['sum']
    assert card['ind'] == OLD_IND, card['ind']
    card['eco']['sum'] = NEW_SUM
    card['ind'] = NEW_IND
    print('g32cfa1d4: eco.sum %r -> %r' % (OLD_SUM, NEW_SUM))
    print('g32cfa1d4: ind %r -> %r' % (OLD_IND, NEW_IND))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('записано')
    return 0


if __name__ == '__main__':
    sys.exit(main())
