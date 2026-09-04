# -*- coding: utf-8 -*-
"""Заметка 502 (консоль, 4 сентября 2026): «Одна сделка, одна карточка,
два покупателя», отвечая на карточку `ga1828730» (Glencore продаёт
31,28% акций «Русснефти» структурам Михаила Гуцериева).

`eco.context` карточки уже нёс находку (месячная очередь): выход
Glencore завершён ДВУМЯ траншами в 2025 году — 12,75% выкупила сама
«Русснефть» через дочернее ООО «Белые ночи» (казначейский пакет), а
12,25% в итоге оказались у Заиры Гудаевой через ООО «Неолайн Активы» —
связь с Гуцериевым лишь косвенная и не подтверждена напрямую. Заголовок
и `buyer` при этом продолжали называть единственным покупателем
«структуры Михаила Гуцериева» — недоказанную, хотя и удобную,
атрибуцию. Владелец подтвердил: одна карточка, но оба реальных
покупателя должны быть названы, а не обобщённая (и не доказанная)
формулировка.

`buyer` (профиль-заглушка «Структуры Михаила Гуцериева») снят —
казначейский пакет отражён `buyer_name` текстом, второй покупатель
(Гудаева) — тоже текстом, оба уже фактически описаны в `eco.context`.

Запуск: python3 pipeline/fix_glencore_russneft_two_buyers.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'ga1828730'
OLD_TITLE = 'Glencore продает 31,28% акций Русснефти структурам Михаила Гуцериева'
NEW_TITLE = 'Glencore вышла из капитала «Русснефти» — казначейский пакет и Заира Гудаева'
OLD_BUYER = 'g3bff5181'


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {c['id']: c for c in data['deals']}
    card = by_id[CARD_ID]
    assert card['title'] == OLD_TITLE, card['title']
    assert card['buyer'] == OLD_BUYER, card['buyer']
    assert card.get('buyer_name') is None

    card['title'] = NEW_TITLE
    card['buyer'] = None
    card['buyer_name'] = ('ООО «Белые ночи» (казначейский пакет «Русснефти», '
                           '12,75%) и Заира Гудаева через ООО «Неолайн '
                           'Активы» (12,25%)')

    print(f'{CARD_ID}: заголовок и покупатель переписаны под двух реальных покупателей')

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Записано.')
    else:
        print('(сухой прогон, для записи — --write)')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
