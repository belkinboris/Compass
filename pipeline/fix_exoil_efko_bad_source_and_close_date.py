# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g549ddd5a («Эксойл»/ЭФКО,
завод «Масленица»): две находки, не подходящие под механизм review.py.

1. Источник `['Max.ru', 'http://max.ru/media_slivki']` — голый адрес
   канала мессенджера MAX без пути к конкретному посту (тот же класс
   дефекта, что уже описан в CLAUDE.md — «домен без пути»). Проверено
   WebFetch: страница отдаёт только описание канала («Бизнес-сливки
   Абирег - Черноземье»), об этой сделке там ни слова. Ссылка удаляется,
   не заменяется — искать конкретный пост канала не удалось.

2. Точная дата фактического закрытия (регистрация в ЕГРЮЛ 27 августа
   2025 года, Интерфакс) не помещается в review.py: единственное
   существующее поле для этого, `eco.context`, — не дословная цитата
   источника, а собственный пересказ карточки, и вставить туда новое
   предложение с сохранением дословности механизм не может (проверено:
   `flat(new)` не лежит в `flat(quote)`, потому что окружающий текст сам
   не дословен). Дата добавляется этим скриптом.
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g549ddd5a'
BAD_SRC = ['Max.ru', 'http://max.ru/media_slivki']
OLD_CONTEXT = ('Помимо этого, в результате сделки ГК «ЭФКО» вместе с '
               'активом приобрело права на широко известные бренды '
               'подсолнечного масла «Олейна», «IDEAL», «Масленица», '
               '«Семеновна», «Сказка» и «Golden Drop», которые пополнили '
               'внушительный портфель потребительских брендов клиента. До '
               '2023 года приобретенный актив являлся дочерней структурой '
               'глобального производителя Bunge.')
NEW_CONTEXT = (OLD_CONTEXT + ' Изменения отражены в ЕГРЮЛ с 27 августа '
               '2025 года.')


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert BAD_SRC in deal['src'], f"{BAD_SRC!r} не найден в src"
    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"

    print(f"{CARD_ID} src: удаляю {BAD_SRC!r} (не про эту сделку)")
    print(f"{CARD_ID} eco.context: += дата регистрации в ЕГРЮЛ (27.08.2025)")

    deal['src'].remove(BAD_SRC)
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
