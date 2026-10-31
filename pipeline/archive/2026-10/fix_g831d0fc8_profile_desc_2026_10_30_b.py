#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Второй шаг к описанию профиля «Резотстрой» (g000e6f6c, покупатель в
карточке g831d0fc8): формат поста берет из описания предложение с именами в
кавычках, и строка «Покупатель» выходила с обрывком «ей же принадлежат…» без
подлежащего. Описание сведено к одному предложению о компании; реестровая
пометка о юрлице остается отдельной. Без ключа — сухой прогон, запись по
--write, assert на старое значение.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
CID = 'g000e6f6c'
OLD = ('Петербургская компания Юлии Карповой, зарегистрирована в январе 2026 года. Ей же принадлежат '
       'гостиничные компании «Курэйтэд» и «Аспен Отель Групп». Юрлицо — АО «Резотстрой».')
NEW = ('Компания Юлии Карповой, которой принадлежат и гостиничные «Курэйтэд» и «Аспен Отель Групп»; '
       'зарегистрирована в Петербурге в январе 2026 года. Юрлицо — АО «Резотстрой».')


def main(write):
    base = json.load(open(PATH, encoding='utf-8'))
    assert base['companies'][CID]['desc'] == OLD, base['companies'][CID]['desc']
    base['companies'][CID]['desc'] = NEW
    print('%s %s -> %s' % ('ПИШЕМ' if write else 'СУХО', CID, NEW))
    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(base, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
