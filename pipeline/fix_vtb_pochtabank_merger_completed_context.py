# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g06a6081f (ВТБ выкупил
49,99% долю «Почты России» в Почта Банке, декабрь 2024): дельта-поиск
подтвердил, что заявленный в карточке план присоединения реализован.
Акционеры ВТБ одобрили присоединение 20 февраля 2026 года, а с 1 мая
2026 года «Почта Банк» юридически прекратил существование как отдельное
юрлицо — вся сеть работает под брендом ВТБ (Ведомости, RB.ru,
1000bankov.ru). Карточка описывает БОЛЕЕ РАННЮЮ сделку (покупку доли,
декабрь 2024, тип M&A) — само присоединение как отдельное корпоративное
событие (реорганизация по ст. 57-58 ГК РФ) в эту карточку не переносится
структурно (не меняются type/status/роли сторон), только фиксируется в
`eco.context` как продолжение сюжета; заводить отдельную карточку
«Реорганизация» — решение человека/притока, не этой правки. Не через
review.py: цитаты из ТРЁХ новых источников за разные месяцы 2026 года
объединены в связный абзац.

Запуск: python3 pipeline/fix_vtb_pochtabank_merger_completed_context.py
        python3 pipeline/fix_vtb_pochtabank_merger_completed_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g06a6081f'

OLD_CONTEXT = (
    'Сумма сделки — 36 млрд руб. даже не покроет убытков государственного '
    'почтового оператора: только в 2022 -2024 гг. их объем превысит '
    '47 млрд руб.'
)
CONTEXT_ADDITION = (
    ' Заявленный план присоединения реализован: 20 февраля 2026 года '
    'акционеры ВТБ одобрили присоединение «Почта Банка», а с 1 мая 2026 '
    'года он юридически прекратил существование как отдельное юрлицо — '
    'вся сеть (около 23 тыс. точек, 19 тыс. банкоматов объединённой сети) '
    'работает под брендом ВТБ.'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['Ведомости', 'https://www.vedomosti.ru/finance/news/2026/05/04/1194877-vtb-prisoedinil-bank'],
    ['RB.ru', 'https://rb.ru/news/vtb-zavershil-prisoedinenie-pochta-banka-teper-23-tys-ofisov-po-vsej-rossii-rabotayut-pod-brendom-vtb/'],
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
