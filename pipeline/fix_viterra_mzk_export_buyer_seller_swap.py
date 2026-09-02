# -*- coding: utf-8 -*-
"""Найдено при дочитывании ga13c3ea7 (Viterra/Тамань) — карточка
g4612b667 («Российский менеджмент Viterra выкупил операционный бизнес
и зерновой терминал в Ростове-на-Дону») несла `buyer` = профиль
`g1a6194cd` («Viterra (российский бизнес)»). Это профиль ПРОДАВЦА
(цели сделки), а не покупателя: заголовок карточки прямо говорит, что
покупатель — «российский менеджмент Viterra», то есть управляющая
компания «Управление агробизнесом» (Демьянов, Кондаков, Долгов, Зень,
Харитонов, см. `law.struct` этой же карточки), а Viterra — сторона,
которую покупают/у которой покупают бизнес.

Родня уже записанного класса уроков «Стороной сделки может быть
записан профиль совсем другой сущности» — только здесь перепутаны не
разные сущности, а РОЛИ одной и той же: та же компания Viterra
корректно стоит SELLER_ID в сестринской карточке ga13c3ea7 (продажа
доли в Таманском терминале, тот же самый выход Viterra из России) — то
есть профиль верный, спутана роль именно в этой карточке.

Профиль для «Управление агробизнесом» не заводится (лишний профиль
ради одной сделки не стоит, см. правило CLAUDE.md) — покупатель
записывается текстом (`buyer_name`), продавец — ссылкой на уже
существующий профиль Viterra (`seller_id`, текст `seller` для
единообразия с сестринской карточкой).

Проверка перед записью: `assert` на исходные (ошибочные) значения.

Запуск: python3 pipeline/fix_viterra_mzk_export_buyer_seller_swap.py
        python3 pipeline/fix_viterra_mzk_export_buyer_seller_swap.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g4612b667'
VITERRA_ID = 'g1a6194cd'


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['buyer'] == VITERRA_ID
    assert deal.get('buyer_name') is None
    assert deal.get('seller') is None
    assert deal.get('seller_id') is None

    print('=== было ===')
    print('buyer:', deal['buyer'], '| buyer_name:', deal.get('buyer_name'))
    print('seller:', deal.get('seller'), '| seller_id:', deal.get('seller_id'))
    print('=== станет ===')
    print('buyer: null | buyer_name: «Управление агробизнесом» (менеджмент Viterra)')
    print('seller: «Viterra» | seller_id:', VITERRA_ID)

    if write:
        deal['buyer'] = None
        deal['buyer_name'] = 'Управление агробизнесом (менеджмент Viterra)'
        deal['seller'] = 'Viterra'
        deal['seller_id'] = VITERRA_ID
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
