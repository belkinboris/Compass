# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка g037385e2
(«ГК Softline приобрела контрольный пакет (50,1%) ГК Борлас») — верхнее
поле `sum` уже несло точную сумму («1,62 млрд ₽», внесена записью
`FIXES` в pipeline/ingest/fixes/batch_agents059_r9.py), а `eco.sum` —
линза «Экономист» — по-прежнему стояла заглушкой «Не раскрыта». Тот же
факт читатель видел на «Обзоре» и не видел на «Экономисте» (родня уже
записанного в CLAUDE.md урока «Сумма на «Обзоре» и сумма в «Экономисте»
— два разных поля»).

Проверено лично прямым WebFetch (CNews, https://www.cnews.ru/news/top/2024-04-03_softlajn_potratil_16_milliarda
— тот же источник, что уже подтвердил `sum`): «Тогда «Софтлайн»
получила 50,1% в «Борлас АФС» за 1,62 млрд руб.»

Запуск: python3 pipeline/fix_softline_borlas_sum_sync.py
        python3 pipeline/fix_softline_borlas_sum_sync.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g037385e2'

OLD_ECO_SUM = 'Не раскрыта'
NEW_ECO_SUM = '1,62 млрд ₽'

NEW_SRC = [
    ['CNews', 'https://www.cnews.ru/news/top/2024-04-03_softlajn_potratil_16_milliarda'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['sum'] == '1,62 млрд ₽'
    assert deal['eco']['sum'] == OLD_ECO_SUM

    already_has_src = any(s[1] == NEW_SRC[0][1] for s in deal['src'])
    new_src = deal['src'] if already_has_src else deal['src'] + NEW_SRC

    print('=== eco.sum: станет ===')
    print(NEW_ECO_SUM)
    if not already_has_src:
        print('\n=== src: добавится ===')
        for s in NEW_SRC:
            print(s)

    if write:
        deal['eco']['sum'] = NEW_ECO_SUM
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
