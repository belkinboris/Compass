# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g7f396659 (структура
Р-Фарм купила 49,9% сети клиник «Центр ЭКО»): дельта-поиск нашёл, что
29 мая 2026 года та же структура (АО «Эко Холдинг») выкупила оставшиеся
50,1% у Сергея Лебедева — теперь Р-Фарм владеет сетью на 100%. Сумма ни
одной из двух сделок не раскрыта; появились две несовпадающие
экспертные оценки (800–900 млн ₽ за 49,9% и 1,6–1,8 млрд ₽ за 100%),
обе — оценки, не факт. Не через review.py: новый источник (vademec.ru,
июнь 2026) описывает СЛЕДУЮЩИЙ этап сделки, а не саму карточку.

Запуск: python3 pipeline/fix_rfarm_centrreko_full_buyout_context.py
        python3 pipeline/fix_rfarm_centrreko_full_buyout_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g7f396659'

OLD_CONTEXT = (
    'Всего в России циклы ВРТ проводятся примерно в 330 клиниках ЭКО, '
    'причем около 70% из них – частные. Объем рынка в стране оценивается '
    'в 25–27 млрд рублей. Крупнейший оператор сегмента – сеть клиник '
    '«Мать и дитя» Марка Курцера.'
)
CONTEXT_ADDITION = (
    ' 29 мая 2026 года та же структура — АО «Эко Холдинг» (входит в '
    'ГК «Р-Фарм») — выкупила у Сергея Лебедева оставшиеся 50,1% акций '
    '«Центр ЭКО», доведя долю до 100%; сумма сделки не раскрывалась. '
    'Выручка сети за 2025 год превысила 2,3 млрд руб. Эксперты '
    'разошлись в оценке: 800–900 млн ₽ за пакет 49,9% (декабрь 2024) '
    'против 1,6–1,8 млрд ₽ за всю группу целиком (оценка на май 2026) '
    '— обе цифры экспертные, не объявленная цена.'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['vademec.ru', 'https://www.vademec.ru/news/2026/06/03/r-farm-polnostyu-vykupil-set-klinik-tsentr-eko/'],
    ['vedomosti.ru', 'https://www.vedomosti.ru/business/articles/2026/06/03/1202336-struktura-gk-r-farm-polnostyu-vikupila-set-klinik'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
