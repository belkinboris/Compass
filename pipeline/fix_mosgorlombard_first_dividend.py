# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g572a4aca (IPO
Мосгорломбарда): дельта-поиск нашёл первую выплату дивидендов после
IPO — раньше в карточке о них не было ни слова.

Не через review.py: `law.terms` уже не пуст (условия самого IPO-
размещения), а факт о дивидендах — из другого, гораздо более позднего
источника.
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g572a4aca'
OLD_TERMS = (
    'С 21 декабря компания прекратила сбор заявок на приобретение акций '
    'по цене от 3,1 до 3,5 руб. и объявила новый сбор с ценовым '
    'диапазоном на уровне 2,5–2,55 руб. за бумагу. Изначально МГКЛ '
    'планировала, что доля free-float по итогам размещения могла '
    'приблизиться к 36%, затем прогноз понизили до 29%.'
)
ADDITION = (
    'Совет директоров ПАО «МГКЛ» («Мосгорломбард») рекомендовал общему '
    'собранию акционеров выплатить годовые дивиденды по итогам 2025 г. '
    'в размере 0,28 руб. на каждую обыкновенную акцию. Об этом '
    'сообщается на сайте центра раскрытия корпоративной информации. '
    'Всего на выплаты рекомендовано направить 355,2 млн руб. или 49% от '
    'чистой прибыли, сообщили в компании «Ведомостям».'
)
NEW_TERMS = OLD_TERMS + ' ' + ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['law']['terms'] == OLD_TERMS, \
        f"law.terms: неожиданное значение {deal['law']['terms']!r}"

    print(f"{CARD_ID} law.terms: += первый дивиденд после IPO (0,28 ₽/"
          "акция по итогам 2025 года, 49% чистой прибыли)")
    deal['law']['terms'] = NEW_TERMS

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО")
    else:
        print("Сухой прогон. Запись — с --write.")


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
