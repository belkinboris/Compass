#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Слияние дубля `g54d92fdd`→`g4803e120` (см. `merge_invitro_mironchik_dup.py`,
28 августа 2026) продублировало факт: `eco.val` уже нёс оценку Peregrine
Capital (12–15 млрд руб., 5–6 EBITDA за 2022 год) с 23 августа 2026
(`fix_invitro_third_valuation.py`, другая формулировка того же
предложения из ТОГО ЖЕ источника, kommersant.ru), а перенос из дубля
дописал ту же цифру ЕЩЁ РАЗ, другими словами, следом. Проверка
дословности в `merge_invitro_mironchik_dup.py` сравнивала добавляемое
предложение только с текстом карточки-дубля — не с уже существующим
текстом карточки-получателя, поэтому не поймала повтор (родня уже
записанного в CLAUDE.md урока «Прежде чем наполнять поле, проверьте, не
показан ли факт под другой подписью»).

Снимает только ВТОРОЕ, задвоенное предложение — первое (с 23 августа,
органично встроенное во фразу «оценил ниже —») остаётся.

Запуск:
    python3 pipeline/fix_invitro_duplicate_peregrine_sentence.py            # сухой прогон
    python3 pipeline/fix_invitro_duplicate_peregrine_sentence.py --write    # записать
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'
CARD_ID = 'g4803e120'

DUPLICATE_TAIL = (' Управляющий директор Peregrine Capital Дмитрий Габышев оценил стоимость '
                   '«Инвитро» в 12–15 млрд руб. или 5–6 EBITDA за 2022 год.')

BAD_VALUE = (
    'Сумма сделки неизвестна. Она может превышать 40 млрд руб., считает генеральный директор '
    '«Infoline-аналитики» Михаил Бурмистров. Однако генеральный директор DSM Group Сергей Шуляк '
    'предполагает, что стороны могли договориться и на 30 млрд руб. Управляющий директор '
    'Peregrine Capital Дмитрий Габышев оценил стоимость «Инвитро» ниже — в 12–15 млрд руб., '
    'или 5–6 EBITDA за 2022 год.' + DUPLICATE_TAIL
)


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next((d for d in data['deals'] if d['id'] == CARD_ID), None)
    assert deal is not None, 'карточки нет'
    assert deal['eco']['val'] == BAD_VALUE, 'значение уже изменилось — правка не нужна или устарела'
    assert deal['eco']['val'].endswith(DUPLICATE_TAIL)

    fixed = deal['eco']['val'][: -len(DUPLICATE_TAIL)]
    print('Было (хвост):', repr(deal['eco']['val'][-160:]))
    print('Станет:', repr(fixed[-160:]))

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return

    deal['eco']['val'] = fixed
    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('\nЗаписано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
