# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g8a66f3c7 (Рег.ру/
Reddock): дельта-поиск дописывает в eco.context, ПОЧЕМУ владелец Reddock
согласился на сделку (его собственная цитата CNews) и что сделка —
не разовая, а часть серии: спустя два месяца Рег.ру повторил тот же ход
с другим провайдером, Eternalhost (ComNews).

Источники: CNews (цитата владельца Reddock Дмитрия Юзепчука) и ComNews
(сделка с Eternalhost, апрель 2024) — оба читал напрямую.
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g8a66f3c7'
OLD_CONTEXT = (
    'Рег.ру занимает около 15% рынка хостинга в домене .RU, количество '
    'клиентов превышает 200 тыс.'
)
ADDITION = (
    '«Рынок хостинга изменился, и мы пришли к решению прекратить '
    'развитие провайдерских услуг. При этом мы осознаем свою '
    'ответственность перед клиентами и поэтому решили доверить их '
    '«Рег.ру» как компании, чей уровень сервисов и линейка продуктов '
    'соответствуют высоким запросам пользователей», — сказал Дмитрий '
    'Юзепчук, владелец компании Reddock. Спустя два месяца Рег.ру '
    'заключил похожую сделку с ещё одним провайдером, Eternalhost, '
    'владелец которого объяснил решение теми же причинами: «Требования '
    'к хостинг-провайдерам со стороны государства постоянно растут, '
    'следовать им становится под силу только наиболее крупным и '
    'технически защищенным компаниям, таким как Рег.ру».'
)
NEW_CONTEXT = OLD_CONTEXT + ' ' + ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"

    print(f"{CARD_ID} eco.context: += причина продажи (цитата владельца "
          "Reddock) и повторная сделка Рег.ру с Eternalhost")
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
