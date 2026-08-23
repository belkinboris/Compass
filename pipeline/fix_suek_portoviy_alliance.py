# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка gf76413f3 (СУЭК/
портовые активы): дельта-поиск нашёл, КАКАЯ структура стала новой
управляющей компанией портов — law.struct называл только сами
терминалы, но не покупателя.

Источник: ABN (15 июля 2024) — читал напрямую.
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gf76413f3'
OLD_STRUCT = (
    'Сделка включает в себя портовые терминалы в портах Мурманск, '
    'Ванино, Восточный и Туапсе.'
)
ADDITION = (
    'Мурманский морской торговый порт сменил управляющую компанию на '
    'АО «Портовый Альянс». Вместе с ним приобрели новую управляющую '
    'компанию Ванинский балкерный терминал АО «Дальтрансуголь», ООО '
    '«МБТ», ООО «Туапсинский балкерный терминал», ООО Стивидорная '
    'Компания «Малый Порт». Ранее данными компаниями управляла — новая '
    'транспортно-логистическая компания АО «НТК». Изменения в ЕГРЮЛ '
    'зафиксированы 12 июля 2024 года; пост гендиректора «Портового '
    'Альянса» занимает с 2 июля 2024 года Михаил Кузнецов.'
)
NEW_STRUCT = OLD_STRUCT + ' ' + ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['law']['struct'] == OLD_STRUCT, \
        f"law.struct: неожиданное значение {deal['law']['struct']!r}"

    print(f"{CARD_ID} law.struct: += новая управляющая компания "
          "(АО «Портовый Альянс»)")
    deal['law']['struct'] = NEW_STRUCT

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО")
    else:
        print("Сухой прогон. Запись — с --write.")


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
