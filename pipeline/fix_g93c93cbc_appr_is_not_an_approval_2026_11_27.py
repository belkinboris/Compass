# -*- coding: utf-8 -*-
"""Карточка g93c93cbc (очередь pending.json): «Согласования» (law.appr) несли
порядок обжалования решения суда — это не согласование (второе чтение
27 ноября 2026; тот же случай — pipeline/archive/2026-11/fix_gf2b576fb_appr_is_not_an_approval.py).
Фраза об обжаловании перенесена в law.terms через write_card.py; здесь поле
возвращается к «—», а запись о нем убрана из fixes/written_2026_11_27_vm.py,
чтобы review.py не вернул текст.

Запуск: python3 pipeline/fix_g93c93cbc_appr_is_not_an_approval_2026_11_27.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')
OLD = 'Ответчики могут обжаловать решение в Челябинском областном суде, срок обжалования — месяц.'


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))   # читаем прямо перед записью
    card = next(c for c in data['cards'] if c['id'] == 'g93c93cbc')
    if card['law']['appr'] == '—':
        print('уже записано')
        return 0
    assert card['law']['appr'] == OLD, card['law']['appr']
    assert 'может быть оспорено' in card['law']['terms']
    card['law']['appr'] = '—'
    if write:
        json.dump(data, open(PATH, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('ЗАПИСАНО: law.appr -> «—»')
    else:
        print('Сухой прогон.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
