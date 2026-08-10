# -*- coding: utf-8 -*-
"""Карточка `c220a77df` (Mars/завод соусов в Луховицах): `eco.sum` нёс
«370 млн ₽» без пометки «(по оценке)», хотя единственный источник
(kommersant.ru/doc/5773585) прямо называет эту сумму оценкой продавца,
а не согласованной ценой: «Актив оценивается продавцом в 370 млн руб.».

Верхнеуровневое `sum` этой же карточки правится через review.py FIXES
(`pipeline/ingest/fixes/batch_e_n06.py`) — там проверка `sum_is_supported()`
сама разрешает пометку «(по оценке)» по слову «оценивается». Для `eco.sum`
review.py требует дословного вхождения пометки в цитату (см. CLAUDE.md:
«у review.py для sum и eco.sum — разные проверки»), а слов «по оценке»
рядом с числом в этой цитате нет — отсюда отдельный скрипт.

Запуск: python3 pipeline/fix_mars_sum_estimate.py
        python3 pipeline/fix_mars_sum_estimate.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

CARD_ID = 'c220a77df'


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == CARD_ID)
    if card['eco']['sum'] == '370 млн ₽ (по оценке)':
        print('УЖЕ ПРИМЕНЕНО %s' % CARD_ID)
        return
    assert card['eco']['sum'] == '370 млн ₽', 'eco.sum уже другое'
    print('ПРАВИМ  %s eco.sum: «370 млн ₽» -> «370 млн ₽ (по оценке)»' % CARD_ID)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    card['eco']['sum'] = '370 млн ₽ (по оценке)'
    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
