# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g334b5760 («Рексофт»
приобрела интегратора ПО «Амара Лаб»): дельта-поиск подтвердил, что
Васильев остаётся партнёром группы (уже известный факт, теперь и на
актуальной странице персон Рексофт), нашёл итоговую выручку группы за
2025 год (первый полный год после сделки) и косвенный признак
интеграции — собственный сайт «Амара Лаб» больше не работает отдельно
и редиректит на сайт Рексофт. Отдельный вклад именно «Амара Лаб» в
выручку группы нигде не выделен — это ожидаемо для непубличной
дочерней структуры, не повод писать цифру, которой нет. Не через
review.py: цитата из НОВОГО источника (reksoft.com/news) в поле,
которое уже содержит текст из другого источника.

Запуск: python3 pipeline/fix_reksoft_amaralab_context_extend.py
        python3 pipeline/fix_reksoft_amaralab_context_extend.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g334b5760'

OLD_CONTEXT = (
    'Основатель «Амара Лаб» Дмитрий Васильев продолжит курировать '
    'развитие бизнеса компании, а также будет отвечать за продажи и '
    'маркетинг всей группы «Рексофт» в статусе партнера.'
)
CONTEXT_ADDITION = (
    ' По итогам 2025 года — первого полного года после сделки —'
    ' выручка группы «Рексофт» выросла на 9%, до 7,35 млрд руб. по '
    'МСФО (более 65% пришлось на заказную разработку); вклад именно '
    '«Амара Лаб» в отчёте отдельно не выделен. Собственный сайт «Амара '
    'Лаб» перестал работать как отдельный ресурс и переадресует на '
    'сайт Рексофт.'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = ['reksoft.com', 'https://www.reksoft.com/news/reksoft-summed-up-the-results-of-2025/']


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_CONTEXT
    assert not any(s[1] == NEW_SRC[1] for s in deal['src'])

    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===', NEW_SRC)

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].append(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
