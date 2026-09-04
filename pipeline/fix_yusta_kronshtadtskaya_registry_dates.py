# -*- coding: utf-8 -*-
"""Недельная очередь (REVISION_BRIEF, второй уровень), карточка
`gabdbe320` («Петербургский логистический холдинг «ЮСТА» приобрел
кондитерскую фабрику в Кронштадте») — карточка уже подробно описана
(выручка, прибыль, цитата покупателя, оценка суммы); `law.struct`
пустовал, а точные регистровые даты перехода прав известны.

Проверено лично прямым WebFetch (saby.ru,
https://saby.ru/profile/7843003738-781001001, реестровый агрегатор,
не пресса): «Бартош Станислав Юрьевич» стал владельцем 11 августа
2026 года; «Черемушкин Дмитрий Анатольевич» назначен гендиректором 20
августа 2026 года. Это ДВА отдельных шага одной сделки (сначала смена
собственника, потом смена руководства), а не два события — согласуется
с уже стоящей в карточке структурой (100% долей, прежний владелец и
гендиректор — Владислав Теплоухов).

НЕ ВНЕСЕНО: изменение поля `date` карточки (28.08.2026, вероятно дата
публикации Mergers.ru) — регистровые даты (11 и 20 августа) не
противоречат ей настолько однозначно, как в других находках этого
прогона: сделка могла считаться закрытой/публично раскрытой уже
после завершения обоих регистровых шагов, и менять дату по одной
находке агрегатора — решение не для этого скрипта. Данные о выручке
за 2025 год у саб-агента разошлись между двумя запросами одной и той
же живой страницы (446,6 vs 453,6 млн ₽) — уже стоящая в карточке
цифра (446 млн ₽, со ссылкой на отчётность самой компании) точнее
любого из этих чтений и не меняется.

Запуск: python3 pipeline/fix_yusta_kronshtadtskaya_registry_dates.py
        python3 pipeline/fix_yusta_kronshtadtskaya_registry_dates.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gabdbe320'

OLD_LAW_STRUCT = '—'
NEW_LAW_STRUCT = (
    'По данным реестрового агрегатора (не прессы), переход прав шёл в'
    ' два шага: 11 августа 2026 года владельцем ООО «КФ'
    ' „Кронштадтская“» стал Станислав Бартош (совладелец и'
    ' гендиректор «ЮСТА»), 20 августа 2026 года гендиректором'
    ' назначен Дмитрий Черемушкин.'
)

NEW_SRC = [
    ['saby.ru', 'https://saby.ru/profile/7843003738-781001001'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['law']['struct'] == OLD_LAW_STRUCT

    existing_urls = {s[1] for s in deal['src']}
    add_src = [s for s in NEW_SRC if s[1] not in existing_urls]
    new_src = deal['src'] + add_src

    print('=== law.struct: станет ===')
    print(NEW_LAW_STRUCT)
    if add_src:
        print('\n=== src: добавится ===')
        for s in add_src:
            print(s)

    if write:
        deal['law']['struct'] = NEW_LAW_STRUCT
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
