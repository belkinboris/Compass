# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
ge33ed8f0 («Урал-Логистика» приобрела 100% «РэйлСпецТранс») — судьба
компании после смены собственника не была отражена. Проверено лично
прямым WebFetch собственного сайта компании.

`eco.context` (дополнено). На момент сделки (2024) парк «РэйлСпецТранс»
насчитывал «более 5 тыс. вагонов» (уже в карточке). Собственный сайт
компании прямо датирует рост парка 2024 годом: дословно
(railst.ru/about/): «2024: Парк крытых вагонов превысил отметку в
6 000 единиц.» — подтверждено ДВАЖДЫ прямым WebFetch с разными
формулировками запроса, дата привязана явно, а не предположительно
(это важно: сама компания и раньше называла себя «лидером рынка
большекубовых крытых вагонов», 2021 год, поэтому без явной привязки
года цифру нельзя было бы датировать).

НЕ ВКЛЮЧЕНО: сумма сделки, независимая оценка, консультанты, судьба
Сергея Смыслова после продажи — не найдены ни в одном источнике
(Интерфакс, Металлоснабжение и сбыт, InfoLine); собственный сайт
«Урал-Логистики» и агрегаторы (list-org.com, audit-it.ru) не добавили
новых фактов о бенефициаре сверх уже известного (Александр Иванов).

Запуск: python3 pipeline/fix_railspetstrans_fleet_growth.py
        python3 pipeline/fix_railspetstrans_fleet_growth.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'ge33ed8f0'

OLD_CONTEXT = (
    'Согласно последней раскрытой отчетности РСТ — за 2022 год, на '
    'конец этого периода в равных долях компанией владели сооснователь '
    'группы Rail Garant Сергей Смыслов и Сергей Сапожников.'
)
NEW_CONTEXT = OLD_CONTEXT + (
    ' К 2024 году, уже под новым собственником, парк крытых вагонов '
    '«РэйлСпецТранс» превысил 6000 единиц — рост с «более 5 тыс.» на '
    'момент сделки (railst.ru).'
)

NEW_SRC = [
    ['railst.ru', 'https://railst.ru/about/'],
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
    print('\n=== src добавится ===')
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
