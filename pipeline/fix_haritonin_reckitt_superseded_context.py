# -*- coding: utf-8 -*-
"""Месячная очередь, карточка ge361bfa8 (структуры Виктора Харитонина/
российский бизнес Reckitt, обсуждается с мая 2026): дельта-поиск
нашёл, что переговоры Харитонина, судя по всему, не привели к сделке —
Reckitt Benckiser 24 июля 2026 года объявила о продаже своих активов
ДРУГОМУ покупателю, группе «Арнест» (карточка gmru-arnest-reckitt).
Ни Харитонин, ни «Фармстандарт» не упоминаются ни в одном источнике о
сделке с «Арнестом». Тот же класс, что уже описан в «Известных
проблемах» (БКС/«Форштадт», Махмудов/«Аквариус»): молчание + смена
контрагента, а не прямое опровержение — STATUS_WORDS не даёт
механически сменить статус на «Не состоялась», решение — за
человеком (см. новую запись в «Известных проблемах» CLAUDE.md).

Не через `review.py`: источники (abn.agency, Коммерсантъ) новые, не
образуют с уже записанным текстом `eco.context` непрерывный кусок.

Источники — читал напрямую (WebFetch, дословные цитаты подтверждены):
https://abn.agency/2026/07/24/reckitt-benckiser-prodast-rossijskij-biznes-po-proizvodstvu-sredstv-gigieny-kompanii-arnest/
https://www.kommersant.ru/doc/8833558

Запуск: python3 pipeline/fix_haritonin_reckitt_superseded_context.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'ge361bfa8'

OLD_CONTEXT = (
    'Отказ Reckitt передать права на глобальные бренды российским '
    'покупателям мог сорвать переговоры по продаже ее '
    'фармацевтических активов структурам основателя «Фармстандарта» '
    'Виктора Харитонина, считает господин Астафьев.'
)
CONTEXT_ADDITION = (
    ' 24 июля 2026 года стало известно, что Reckitt Benckiser '
    'договорилась о продаже российского подразделения в сегменте '
    'бытовой химии не структурам Харитонина, а группе «Арнест» — '
    'закрытие этой сделки ожидается во второй половине 2026 года. Ни '
    'Харитонин, ни «Фармстандарт» в сообщениях об этой сделке не '
    'упоминаются.'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"

    print(f'{CARD_ID} eco.context: += актив ушёл другому покупателю '
          f'(«Арнест»)')

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('ЗАПИСАНО')
    else:
        print('Сухой прогон. Запись — с --write.')


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
