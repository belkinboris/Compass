# -*- coding: utf-8 -*-
"""Месячная очередь, карточка g5dc6cb47 (ОСК/КМЗ): дельта-поиск нашёл
вторую, куда более точную и низкую независимую оценку сделки — уже
известная оценка Коммерсанта («порядка 1 млрд рублей») была общей
догадкой, а аналитик телеграм-канала Bonus Fabula Дмитрий Кумановский
объясняет логику цены (менеджмент и портфель заказов не менялись —
ОСК фактически платила за документацию и обучение проектировщиков) и
даёт куда более узкий диапазон. Не через review.py: поле eco.val уже
несёт содержание, второй источник не образует с ним непрерывный кусок
текста.

Источник — читал напрямую (fetch_article_texts.py, закэширован):
https://www.fontanka.ru/2026/01/14/76215445/

Запуск: python3 pipeline/fix_kmz_osk_kumanovsky_valuation.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g5dc6cb47'

OLD_VAL = (
    'Сумма сделки не раскрывается. По мнению экспертов, она могла '
    'составить порядка 1 млрд рублей, писал «Коммерсантъ».'
)
ADDITION = (
    'Аналитик телеграм-канала Bonus Fabula Дмитрий Кумановский '
    'предполагает цену ниже: «Поскольку менеджмент КМЗ после покупки не '
    'менялся, вмешательств в портфель заказов тоже не было. Фактически '
    'ОСК платила за использование документации и обучение '
    'проектировщиков. Поэтому цена предприятия в сделке могла быть '
    'невысокой — около стоимости чистых активов или 10% от выручки — '
    'порядка 680–700 млн рублей».'
)
NEW_VAL = OLD_VAL + ' ' + ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['val'] == OLD_VAL, \
        f"eco.val: неожиданное значение {deal['eco']['val']!r}"

    print(f"{CARD_ID} eco.val: += вторая, более узкая и низкая оценка "
          f"(Дмитрий Кумановский, 680-700 млн ₽)")
    deal['eco']['val'] = NEW_VAL

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО")
    else:
        print("Сухой прогон. Запись — с --write.")


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
