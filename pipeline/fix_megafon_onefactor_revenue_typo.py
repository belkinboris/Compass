# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g54dc2165 (Мегафон/oneFactor):
`eco.target_fin` дословно повторял цифру источника rb.ru — «выручка... 11,4
млрд рублей (против 792 млн в 2020 году)» — но сам rb.ru внутренне
противоречив: рост с 792 млн до 11,4 млрд — это рост в 14,4 раза, а не
правдоподобный годовой скачок для такой компании.

Второй независимый источник (adindex.ru, со ссылкой на данные ФНС) даёт
другую цифру: «выручка компании... за 2021 г. выросла на 78,9%, до 1,4 млрд
руб.» — и это СОГЛАСУЕТСЯ с базой 792 млн: 792 × 1,789 ≈ 1417 млн ≈ 1,4 млрд.
У rb.ru, по всей видимости, опечатка (лишняя цифра «1»: «11,4» вместо «1,4»).
Цифра чистой прибыли (898,6 млн) совпадает у обоих источников — трогать
не нужно.

Это не правка через review.py: исправление опирается на СРАВНЕНИЕ ДВУХ
источников и на арифметическую проверку, а не на дословную цитату ОДНОГО
источника, — review.py такой класс правок не проверяет (см. CLAUDE.md,
раздел «Источник может расходиться сам с собой»).
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g54dc2165'
OLD_TARGET_FIN = ('Выручка компании по итогам 2021 года составила 11,4 '
                   'млрд рублей (против 792 млн в 2020 году), чистая '
                   'прибыль — 898,6 млн рублей (против 335,6 млн в 2020 '
                   'году)')
NEW_TARGET_FIN = ('Выручка компании по итогам 2021 года составила 1,4 '
                   'млрд рублей (против 792 млн в 2020 году), чистая '
                   'прибыль — 898,6 млн рублей (против 335,6 млн в 2020 '
                   'году)')


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['target_fin'] == OLD_TARGET_FIN, \
        f"eco.target_fin: неожиданное значение {deal['eco']['target_fin']!r}"

    print(f"{CARD_ID} eco.target_fin: 11,4 млрд -> 1,4 млрд "
          "(опечатка источника rb.ru, поправлено по adindex.ru + арифметике)")
    deal['eco']['target_fin'] = NEW_TARGET_FIN

    src_urls = [s[1] for s in deal.get('src', [])]
    new_src = ['AdIndex', 'https://adindex.ru/news/digital/2022/12/28/309709.phtml']
    if new_src[1] not in src_urls:
        deal['src'].append(new_src)
        print(f"{CARD_ID} src: += AdIndex (второй независимый источник, "
              "подтверждает верную цифру выручки)")

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО")
    else:
        print("Сухой прогон. Запись — с --write.")


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
