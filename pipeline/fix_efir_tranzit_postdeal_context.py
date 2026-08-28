# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка gf7dede20 (Группа Russ
приобрела ООО «Эфир Транзит» — оператора рекламы на станциях казанского
метро): дельта-поиск нашёл судьбу цели после сделки — юрлицо формально
прекратило существование, а покупатель продолжил консолидацию того же
рынка. Все цитаты подтверждены лично прямым WebFetch.

1. ООО «Эфир Транзит» прекратило существование путём присоединения к
   покупателю 14 февраля 2025 года, через 5 месяцев после сделки
   (Audit-it.ru).
2. Через год Russ купил ВТОРОГО оператора рекламы в казанском метро —
   «Барсрекарт» (октябрь 2025) — и планирует интегрировать её инвентарь в
   свою сеть (Коммерсантъ).

Сумму сделки и консультантов дельта-поиск не нашёл ни в одном источнике —
честная пустота, не тронуто.

Запуск: python3 pipeline/fix_efir_tranzit_postdeal_context.py
        python3 pipeline/fix_efir_tranzit_postdeal_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gf7dede20'

OLD_CONTEXT = (
    'До сентября нынешнего года в учредителях казанского «Эфир Транзит» '
    'были 2 человека. Это Глеб Григорьев (50%) и Луиза Сафарова (50%). '
    'Последняя является женой бывшего главы МВД Татарстана Асгата '
    'Сафарова.'
)
CONTEXT_ADDITION = (
    ' ООО «Эфир Транзит» прекратило существование как отдельное юрлицо '
    'путём «реорганизации в форме присоединения (14.02.2025)» — уже через '
    '5 месяцев после сделки (Audit-it.ru). Russ продолжил консолидацию '
    'рынка: «группа Russ (входит в ООО РВБ) в конце октября купила одного '
    'из операторов рекламы метро Казани — компанию «Барсрекарт»», сеть '
    'пополнилась лайтбоксами двух форматов, и компания планирует '
    '«интегрировать рекламный инвентарь «Барсрекарт» в сеть Russ» '
    '(Коммерсантъ).'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['Audit-it.ru', 'https://www.audit-it.ru/contragent/1021603067529_ooo-efir-tranzit'],
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/8157517'],
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
