# -*- coding: utf-8 -*-
"""Rostic's / «Юнирест» (g1f2895c0): оценка инвестбанкира — не цена сделки, сумма «Не раскрыта».

docs/card_money.md, «Что идет в сумму» (13 ноября 2026): оценка аналитика, эксперта,
консультанта — не цена; sum = «Не раскрыта», цифра с автором — в eco.val (она там уже есть:
Илья Шумов — 6–8 млрд ₽, Валерия Попова — около 6,6 млрд ₽). «Коммерсантъ» цену сделки не
называет: «По оценке инвестбанкира Ильи Шумова, 20% в капитале «Юниреста» может стоить около
6–8 млрд руб.» review.py «Не раскрыта» не пишет (ждет число) — поэтому разовый скрипт.
Найдено 18 ноября 2026 при подборе примера для рекламы расчета цены.

    python3 pipeline/archive/2026-11/rostics_sum_undisclosed_2026_11_18.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
OLD, NEW = '6–8 млрд ₽ (по оценке)', 'Не раскрыта'


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))      # перечитано прямо перед записью
    d = next(x for x in data['deals'] if x['id'] == 'g1f2895c0')
    if d['sum'] == NEW and d['eco']['sum'] == NEW:
        print('УЖЕ ПРИМЕНЕНО')
        return 0
    assert d['sum'] == OLD and d['eco']['sum'] == OLD, (d['sum'], d['eco']['sum'])
    assert 'Шумов' in d['eco'].get('val', ''), 'оценка должна остаться в eco.val'
    d['sum'] = d['eco']['sum'] = NEW
    print('g1f2895c0: %s -> %s' % (OLD, NEW))
    if write:
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
