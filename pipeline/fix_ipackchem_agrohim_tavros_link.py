# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка g766a4daf
(Ipackchem продал производство тары для агрохимии ООО «Ипакэм») —
конечный бенефициар покупателя («Управление агроактивами») не был
известен, а в 2024 году пресса и сам предполагаемый бенефициар
разошлись во мнении. Проверено лично прямым WebFetch трёх источников.

`eco.context` (дополнено). В момент сделки (2024) пресса связывала
покупателя с агрохолдингом «Таврос», а сам холдинг это отрицал.
Дословно (glavpahar.ru): «компанию «Управление агроактивами»
связывают с крупным агрохолдингом «Таврос»», «который уже успел
сообщить о том, что к сделке с бывшим активом Ipackchem в РФ он
отношения не имеет». Позже реестр подтвердил именно ту связь, которую
холдинг отрицал: по данным ЕГРЮЛ (audit-it.ru, проверено лично прямым
WebFetch), с 20 мая 2025 года соучредителем ООО «Управление
агроактивами» стало ООО «УК ТАВРОС» — «Новый учредитель – ООО "УК
ТАВРОС"» (дата 20.05.2025). Также перенесены финансовые итоги завода
после смены собственника (star-pro.ru, данные отчётности ООО «Агрохим
Решения», прежнее название — ООО «Ипакэм»): прибыль 2 499 000 ₽ за
2024 год сменилась убытком 29 471 000 ₽ за 2025 год.

НЕ ВКЛЮЧЕНО: смена гендиректора завода в июне 2026 года (Федосеев →
Куперман) — техническая деталь без публично названной причины, не
относится к самой сделке; консультанты и раскрытая сумма сделки —
не найдены ни в одном из проверенных источников (Ipackchem, Forbes,
Lenta.ru, glavpahar.ru).

Запуск: python3 pipeline/fix_ipackchem_agrohim_tavros_link.py
        python3 pipeline/fix_ipackchem_agrohim_tavros_link.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g766a4daf'

OLD_CONTEXT = (
    'после совершения сделки, стоимость которой на момент осуществления '
    'не раскрывается, ООО «Ипакэм» сменило название на ООО «Агрохим '
    'Решения»'
)
NEW_CONTEXT = OLD_CONTEXT + (
    '. В 2024 году, во время самой сделки, СМИ связывали покупателя с '
    'агрохолдингом «Таврос», который это публично отрицал: «компанию '
    '«Управление агроактивами» связывают с крупным агрохолдингом '
    '«Таврос», который уже успел сообщить о том, что к сделке... он '
    'отношения не имеет» (glavpahar.ru). По данным ЕГРЮЛ, с 20 мая 2025 '
    'года соучредителем ООО «Управление агроактивами» стало ООО «УК '
    'ТАВРОС» — реестр подтвердил ту связь, которую холдинг отрицал '
    'годом ранее. По данным отчётности, финансовый результат завода '
    'сменился с прибыли 2,5 млн ₽ в 2024 году на убыток 29,5 млн ₽ в '
    '2025 году.'
)

NEW_SRC = [
    ['glavpahar.ru', 'https://glavpahar.ru/news/proizvoditel-tary-dlya-szr-ipackchem-prodal-rossiyskiy-zavod-v-kirovo-chepecke'],
    ['audit-it.ru', 'https://www.audit-it.ru/contragent/1167746868629_ooo-upravlenie-agroaktivami'],
    ['star-pro.ru', 'https://star-pro.ru/proverka-kontragenta/organization/1174350006863--ooo-agroxim-resheniya'],
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
