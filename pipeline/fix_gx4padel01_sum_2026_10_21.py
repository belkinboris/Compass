# -*- coding: utf-8 -*-
"""X4 Падел/Rocket Padel (gx4padel01): полный pytest нашёл два механических
дефекта на одной карточке.

1. `eco.sum` стоял прочерком, хотя `sum` («Обзор») уже несёт диапазон —
   девятый за пять суток случай пробела `accept_card.py` (`sum_fields_differ`
   не ловит пустой `eco.sum`), записанного в KNOWN_ISSUES.md.
2. Пометка недостоверности в `sum` — «(оценка)», а канонична только
   «(по оценке)» (`test_estimate_note_is_short`); без «по» и без цифры
   внутри скобок пометка читается как длинная/неровная оговорка.

Запись review.FIXES на оба поля проверена заранее — её не было.

Без ключа — сухой прогон, запись по --write.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

OLD_SUM = '120–220 млн ₽ (оценка)'
NEW_SUM = '120–220 млн ₽ (по оценке)'


def main():
    write = '--write' in sys.argv
    data = json.load(open(DATA, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == 'gx4padel01')
    assert card['sum'] == OLD_SUM, card['sum']
    assert card['eco']['sum'] == '—', card['eco']['sum']
    card['sum'] = NEW_SUM
    card['eco']['sum'] = NEW_SUM
    print('gx4padel01: sum %r -> %r' % (OLD_SUM, NEW_SUM))
    print('gx4padel01: eco.sum %r -> %r' % ('—', NEW_SUM))
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
