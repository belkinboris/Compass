# -*- coding: utf-8 -*-
"""Разовая правка g8dfb3aa0 (Supplement Group/«Лейблпак»): опечатка в цитате.

ЧТО НЕВЕРНО. `extra` заканчивался словами «сумма могла быть символической» —
источник (kommersant.ru/doc/8443530) дословно говорит другое:

    «Она могла быть умеренной, учитывая чистые активы компании, не
    исключает гендиректор инвестиционной компании Atomic Capital
    Александр Зайцев.»

«Символической» и «умеренной» — разные по смыслу оценки суммы сделки, не
опечатка на уровне буквы; факт был искажён при разборе источника.

ПОЧЕМУ НЕ ЧЕРЕЗ review.py. Правка меняет одно слово внутри вручную
составленного абзаца (`extra` целиком не является цитатой с одной
страницы) — review.py требует, чтобы ВЕСЬ `new` дословно лежал в `quote`,
а абзац на экране длиннее самой цитаты.

Запуск:
    python3 pipeline/fix_leiblpak_extra_quote.py            # сухой прогон
    python3 pipeline/fix_leiblpak_extra_quote.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ROOT)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g8dfb3aa0'
OLD_EXTRA = ('Сделка находится в процессе закрытия. АО «Сапплемент '
             'Капитал» приобретает ООО «Лейблпак» — производителя '
             'самоклеящихся этикеток с флексографской и высокой печатью. '
             'Гендиректор инвесткомпании Atomic Capital Александр Зайцев '
             'не исключает, что сумма могла быть символической.')
NEW_EXTRA = ('Сделка находится в процессе закрытия. АО «Сапплемент '
             'Капитал» приобретает ООО «Лейблпак» — производителя '
             'самоклеящихся этикеток с флексографской и высокой печатью. '
             'Гендиректор инвесткомпании Atomic Capital Александр Зайцев '
             'не исключает, что сумма могла быть умеренной.')


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['extra'] == OLD_EXTRA, 'extra карточки уже другое'

    print('БЫЛО:', OLD_EXTRA)
    print('СТАНЕТ:', NEW_EXTRA)

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    deal['extra'] = NEW_EXTRA
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
