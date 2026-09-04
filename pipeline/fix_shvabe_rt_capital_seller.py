# -*- coding: utf-8 -*-
"""Недельная очередь (REVISION_BRIEF, второй уровень), карточка
`ge957fc7b` («"Ростех" продает штаб-квартиру "Швабе"», статус
«Обсуждается», торги назначены на 25 сентября 2026 года) —
`law.struct` пустовал, хотя организатор торгов и дата аукциона
названы в источнике.

Проверено лично прямым WebFetch (РИА Недвижимость,
https://realty.ria.ru/20260826/shvabe-2113215916.html):
«РТ-Капитал, занимающейся реализацией непрофильных активов» —
организатор торгов; «Торги назначены на 25 сентября»; здание
«возведенного в 1972 году».

НЕ ВНЕСЕНО: покупатель, результат торгов — на дату этого прогона (3-4
сентября 2026 года) торги ещё не состоялись (назначены на 25
сентября); возможные планы редевелопмента комплекса, упомянутые в
заголовке Ведомостей, — статья за платным доступом, доступна только
треть текста, не подтверждено дословным чтением.

Запуск: python3 pipeline/fix_shvabe_rt_capital_seller.py
        python3 pipeline/fix_shvabe_rt_capital_seller.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'ge957fc7b'

OLD_LAW_STRUCT = '—'
NEW_LAW_STRUCT = (
    'Организатор торгов — «РТ-Капитал», занимающаяся реализацией'
    ' непрофильных активов «Ростеха». Торги назначены на 25 сентября'
    ' 2026 года. Здание возведено в 1972 году.'
)


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['law']['struct'] == OLD_LAW_STRUCT

    print('=== law.struct: станет ===')
    print(NEW_LAW_STRUCT)

    if write:
        deal['law']['struct'] = NEW_LAW_STRUCT
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
