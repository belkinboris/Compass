# -*- coding: utf-8 -*-
"""«Туту» / «Ракета» и IBC (g5d3527dd): сумма снова «Не раскрыта».

18 ноября 2026, 16:55 enrich.py вписал «600 млн ₽» из заголовка Mergers.ru («может вложить
500–600 млн руб.» — оценка аналитика Михаила Бурмистрова), приложив цитату «Коммерсанта» без
числа; читатель при сборке поставил «Не раскрыта» (оценка — в eco.val), пост в канале вышел
с «не раскрывается». Владелец: «почему у нас 600 написано, а в финансах — не раскрыты и по
оценке». Значение добавлено в `retracted`, чтобы обогащение его не вернуло; ошибочная запись
fact_log снята. Сам enrich.py больше не пишет число поверх «Не раскрыта» прочитанной карточки.

    python3 pipeline/archive/2026-11/tutu_sum_undisclosed_2026_11_18.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))      # перечитано прямо перед записью
    d = next(x for x in data['deals'] if x['id'] == 'g5d3527dd')
    if d['sum'] == 'Не раскрыта':
        print('УЖЕ ПРИМЕНЕНО')
        return 0
    assert d['sum'] == '600 млн ₽' and d['eco']['sum'] == '600 млн ₽', (d['sum'], d['eco']['sum'])
    assert 'Бурмистров' in d['eco'].get('val', '')
    d['sum'] = d['eco']['sum'] = 'Не раскрыта'
    ret = d.setdefault('retracted', {}).setdefault('sum', [])
    if '600 млн ₽' not in ret:
        ret.append('600 млн ₽')
    d['fact_log'] = [e for e in d.get('fact_log') or [] if not (e.get('field') == 'sum' and e.get('by') == 'enrich')]
    if not d['fact_log']:
        d.pop('fact_log')
    print('g5d3527dd: 600 млн ₽ -> Не раскрыта; retracted.sum += 600 млн ₽')
    if write:
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
