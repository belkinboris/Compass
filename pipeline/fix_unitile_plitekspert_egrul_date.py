# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка gb207417a (Александр Файн
продал 5% доли в Unitile компании «Плитэксперт»): дельта-поиск нашёл по
ЕГРЮЛ точный механизм и дату сделки — это не прямая передача части доли
Файна, а увеличение уставного капитала «Юнитайл Холдинга» (100 000 →
105 263 руб.) с появлением «Плитэксперта» новым участником на новую
долю, зарегистрированное 21 ноября 2024 года (а не 28 декабря, как было
в карточке). Гипотеза эксперта о безденежной форме оплаты («Эта сделка
могла пройти на безденежной основе») ни подтверждена, ни опровергнута
напрямую — оставлена как есть, добавлен только точный юридический
механизм. Отдельно нашлась более поздняя, не связанная с этой сделкой
реструктуризация: 3 июня 2026 года личная доля Файна (94,99%) перешла
подконтрольному ему же АО «СДМ ИНВЕСТ» (создано в феврале 2025) — смена
формы владения, не продажа. Не через review.py: данные реестра
(audit-it.ru, companies.rbc.ru), а не цитата статьи.

Запуск: python3 pipeline/fix_unitile_plitekspert_egrul_date.py
        python3 pipeline/fix_unitile_plitekspert_egrul_date.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gb207417a'

OLD_DATE = '2024-12-28'
NEW_DATE = '2024-11-21'

OLD_STRUCT = (
    'Эта сделка могла пройти на безденежной основе. Такие механизмы '
    'могут стать популярными из-за текущей высокой стоимости заемных '
    'средств.'
)
STRUCT_ADDITION = (
    ' По данным ЕГРЮЛ, юридически доля оформлена не как передача части '
    'существующей доли Файна, а как увеличение уставного капитала ООО '
    '«Юнитайл Холдинг» со 100 000 до 105 263 руб. — «Плитэксперт» вошёл '
    'новым участником на новую долю (21 ноября 2024 года).'
)
NEW_STRUCT = OLD_STRUCT + STRUCT_ADDITION

OLD_CONTEXT = (
    'Unitile развивается с 1990-х годов. Основным владельцем бизнеса, '
    'согласно СПАРК, выступает Александр Файн. В группу входят '
    'производства общей мощностью 25 млн кв. м в год облицовочной '
    'плитки, керамогранита, декоративных элементов, кирпича, карьеры '
    'для добычи сырья в Ростовской и Воронежской областях. Согласно '
    'Ассоциации производителей керамических материалов, Unitile — на '
    'втором месте по выпуску керамической продукции в России: доля '
    'оценивается в 14,4%. Инвестбанкир Илья Шумов предполагает, что '
    'стоимость бизнеса Unitile — около 6 млрд руб. Осенью прошлого года '
    'стало известно, что Unitile выкупил у PCG основного конкурента — '
    'Quadro Decor. Сумма сделки оценивалась в 600 млн руб.'
)
CONTEXT_ADDITION = (
    ' 3 июня 2026 года личная доля Файна (94,99% в «Юнитайл Холдинге») '
    'перешла подконтрольному ему же АО «СДМ ИНВЕСТ» (создано в феврале '
    '2025 года, единственный учредитель — сам Файн) — это смена формы '
    'владения, а не продажа третьей стороне.'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['audit-it.ru', 'https://www.audit-it.ru/contragent/1186196038269_ooo-yunitayl-kholding'],
    ['companies.rbc.ru', 'https://companies.rbc.ru/id/1257700077447-ao-sdm-invest/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['date'] == OLD_DATE
    assert deal['law']['struct'] == OLD_STRUCT
    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== date ===', NEW_DATE)
    print('=== law.struct: станет ===')
    print(NEW_STRUCT)
    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['date'] = NEW_DATE
        deal['law']['struct'] = NEW_STRUCT
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
