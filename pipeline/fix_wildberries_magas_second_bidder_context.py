# -*- coding: utf-8 -*-
"""Месячная очередь, карточка g97d0d2a2 (Wildberries & Russ/аэропорт
Магас): дельта-поиск нашёл имя второго участника аукциона — карточка
знала только, что участвовали «две компании», без имени проигравшего.
Не через review.py: текущее значение eco.context уже перефразировано
относительно источника (не дословная цитата) и не образует непрерывный
кусок текста с новым источником.

Источник — читал напрямую (fetch_article_texts.py, закэширован):
https://news.ru/regions/kompaniya-iz-struktury-wildberries-vykupila-rossijskij-aeroport
Дословная цитата: «в аукционе на их покупку приняли участие компании
ООО «Апр-Сити/ТВД» и ООО «АБС Холдинг». 18 сентября победителем аукциона
признано ООО «Апр-Сити/ТВД»».

Запуск: python3 pipeline/fix_wildberries_magas_second_bidder_context.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g97d0d2a2'

OLD_CONTEXT = (
    'Изначально акции оценивались в 250 млн рублей, но по итогам '
    'аукциона, в котором участвовали две компании, цена сделки достигла '
    '425 млн рублей. Средства будут направлены на реализацию социальных '
    'программ в нашей республике'
)
CONTEXT_ADDITION = (
    'Вторым участником аукциона, по данным news.ru, было ООО «АБС '
    'Холдинг» — победителем 18 сентября признано ООО «Апр-Сити/ТВД».'
)
NEW_CONTEXT = OLD_CONTEXT + '. ' + CONTEXT_ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"

    print(f"{CARD_ID} eco.context: += имя второго участника аукциона "
          f"(«АБС Холдинг»)")
    deal['eco']['context'] = NEW_CONTEXT

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО")
    else:
        print("Сухой прогон. Запись — с --write.")


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
