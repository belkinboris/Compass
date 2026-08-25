# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g23ff3a09 («Моторика»
купила 50,1% завода по производству инвалидных колясок ЗСО, декабрь
2024): дельта-поиск нашёл, что актив продолжает развиваться внутри
группы — в 2025 году произведено 35,9 тыс. кресел-колясок (годовой отчёт
группы «Моторика»), а в июле 2026 группа привлекла 1 млрд ₽ льготного
финансирования от МСП Банка, одна из целей которого — «развивать
производственный контур на базе «Завода специального оборудования»».
Выручка группы «Моторика» в целом выросла в 2025 году на 70% до 7,1 млрд
руб. (это показатель ГРУППЫ, не отдельно завода — оговорено явно).
Структура собственности ЗСО (три совладельца) не изменилась. Не через
review.py: цифры из НОВЫХ источников (годовой отчёт, пресс-релиз) в поле,
уже содержащем текст из ЕГРЮЛ.

Запуск: python3 pipeline/fix_motorika_zso_2025_growth_context.py
        python3 pipeline/fix_motorika_zso_2025_growth_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g23ff3a09'

OLD_CONTEXT = (
    'До сделки 75,05% долей ООО «ЗСО» принадлежало Николаю Кузнецову, '
    'после нее – 24,95%, следует из выписки из ЕГРЮЛа. Оставшиеся 24,95% '
    'сохранились за Павлом Кузнецовым.'
)
CONTEXT_ADDITION = (
    ' Актив продолжает развиваться внутри группы: в 2025 году завод '
    'произвёл 35,9 тыс. кресел-колясок (годовой отчёт группы «Моторика»), '
    'а в июле 2026 года группа привлекла 1 млрд ₽ льготного '
    'финансирования от МСП Банка — одна из заявленных целей транша: '
    '«развивать производственный контур на базе «Завода специального '
    'оборудования»». Выручка группы «Моторика» в целом выросла в 2025 '
    'году на 70%, до 7,1 млрд руб. (показатель по всей группе, не только '
    'по заводу). Структура собственности ЗСО (три совладельца) с момента '
    'сделки не менялась.'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['Годовой отчёт «Моторика»', 'https://ar2025.motorica.org/'],
    ['re-port.ru', 'https://re-port.ru/pressreleases/gruppa_motorika_privlekla_1_mlrd_rublei_lgotnogo_finansirovanija_v_msp_banke_chto_pozvolit_rasshirit_proizvodstvo_i_uskorit_razvitie_ykosistemy_assistivnyh_tehnologii/'],
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
