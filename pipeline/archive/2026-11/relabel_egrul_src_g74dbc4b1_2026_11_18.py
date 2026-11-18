# -*- coding: utf-8 -*-
"""Карточка g74dbc4b1: подпись источника «ЕГРЮЛ» говорит, куда ведет ссылка.

Владелец, 18 ноября 2026: «где значится "егрюл" почему-то на какой-то рандомный ресурс
переводит, а не на выписку». Ссылка ведет на DataNewton — сайт, который показывает данные
ЕГРЮЛ (участники с долями и ИНН); у egrul.nalog.ru постоянных ссылок на выписку нет.
Подпись теперь называет сайт, чтобы читатель не ждал выписку налоговой.

    python3 pipeline/archive/2026-11/relabel_egrul_src_g74dbc4b1_2026_11_18.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
URL = 'https://datanewton.ru/contragents/1257700437136'
OLD = 'ЕГРЮЛ: ООО «ИММ0РТАЛ», история участников'
NEW = 'Данные ЕГРЮЛ на DataNewton: участники ООО «Иммортал»'


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))      # перечитано прямо перед записью
    deal = next(d for d in data['deals'] if d['id'] == 'g74dbc4b1')
    rows = [s for s in deal['src'] if s[1] == URL]
    assert len(rows) == 1, rows
    if rows[0][0] == NEW:
        print('УЖЕ ПРИМЕНЕНО')
        return 0
    assert rows[0][0] == OLD, rows[0][0]
    rows[0][0] = NEW
    print('%s -> %s' % (OLD, NEW))
    if write:
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
