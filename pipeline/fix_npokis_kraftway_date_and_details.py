# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка ga3e353b1
(НПО КИС (Росатом) приобрело 50% компании Kraftway) — карточка была
почти пуста (только заголовок, покупатель и предмет), а дата стояла с
ошибкой на семь месяцев.

ДАТА. Карточка несла «2024-07-29» — это дата статьи-источника про смену
гендиректора НПО КИС (kommersant.ru/doc/6878096), а не дата самой
сделки. Настоящая дата закрытия найдена во ВТОРОМ материале Коммерсанта
о самой сделке, проверено лично прямым WebFetch
(kommersant.ru/doc/6425675, статья от 25.12.2023): «"Росатом" 22 декабря
закрыл сделку по покупке доли» — то есть 22 декабря 2023 года. Перенос в
другой год не проходит через review.py (правило CLAUDE.md), поэтому
отдельный скрипт с assert на исходное значение.

ДОБАВЛЕНО (карточка была почти пустой, каждый факт — новое поле):
- `seller` (текстом): «Гендиректор и владелец компании Алексей Кравцов
  сохранил 50%» — Кравцов остался совладельцем, а не продал всё.
- `sum`/`eco.val`: «Сумму сделки собеседник "Ъ" оценил в 3,5–5 млрд руб.»
  — оценка со ссылкой на источник, не факт.
- `eco.rationale`: «объединили усилия в вопросах, связанных с
  производством доверенных программно-аппаратных комплексов для
  критической информационной инфраструктуры».
- `eco.context`: история Kraftway («учреждено в 1993 году», выручка «в
  2020 году составила 7,6 млрд руб., чистая прибыль — 2 млрд руб.») и
  план инвестиций («в 2024 году выделить еще порядка 2–3 млрд руб.» на
  модернизацию производства и разработки в микроэлектронике).

НЕ включены: консультанты сделки — не найдены ни в одном источнике;
финансы 2025 года у НПО КИС (материнская структура-покупатель, а не
Kraftway — перенос был бы ошибкой атрибуции, родня урока «Русал/Pioneer»
в CLAUDE.md); несостоявшиеся переговоры Росатома о покупке МЦСТ
(«Эльбрус») — это отдельный, несостоявшийся сюжет, не относится к
предмету этой карточки.

Запуск: python3 pipeline/fix_npokis_kraftway_date_and_details.py
        python3 pipeline/fix_npokis_kraftway_date_and_details.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'ga3e353b1'

OLD_DATE = '2024-07-29'
NEW_DATE = '2023-12-22'

NEW_SELLER = 'Алексей Кравцов'

OLD_SUM = 'Не раскрыта'
NEW_SUM = '3,5–5 млрд ₽ (по оценке)'

NEW_VAL = (
    'Сумму сделки собеседник «Ъ» оценил в 3,5–5 млрд руб. (по оценке).'
)

NEW_RATIONALE = (
    'Стороны «объединили усилия в вопросах, связанных с производством '
    'доверенных программно-аппаратных комплексов для критической '
    'информационной инфраструктуры».'
)

OLD_CONTEXT = '—'
NEW_CONTEXT = (
    'Kraftway учреждено в 1993 году; выручка в 2020 году составила 7,6 '
    'млрд руб., чистая прибыль — 2 млрд руб. В 2024 году «Росатом» '
    'планировал выделить ещё порядка 2–3 млрд руб. на модернизацию '
    'производственных мощностей и разработки в сфере микроэлектроники.'
)

NEW_SRC = [
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/6425675'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['date'] == OLD_DATE
    assert deal.get('seller') is None
    assert deal['sum'] == OLD_SUM
    assert deal['eco']['sum'] == OLD_SUM
    assert deal['eco']['val'] == '—'
    assert not deal['eco'].get('rationale')
    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print(f'=== date: {OLD_DATE!r} -> {NEW_DATE!r} ===')
    print(f'=== seller (новое поле): станет {NEW_SELLER!r} ===')
    print(f'=== sum/eco.sum: {OLD_SUM!r} -> {NEW_SUM!r} ===')
    print('=== eco.val: станет ===')
    print(NEW_VAL)
    print('=== eco.rationale (новое поле): станет ===')
    print(NEW_RATIONALE)
    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['date'] = NEW_DATE
        deal['seller'] = NEW_SELLER
        deal['sum'] = NEW_SUM
        deal['eco']['sum'] = NEW_SUM
        deal['eco']['val'] = NEW_VAL
        deal['eco']['rationale'] = NEW_RATIONALE
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
