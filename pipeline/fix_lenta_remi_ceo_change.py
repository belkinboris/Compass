# -*- coding: utf-8 -*-
"""Месячная очередь, карточка gc3cb0d4d («Лента»/«Реми»): дельта-поиск
нашёл, что после закрытия сделки сменился генеральный директор ООО
«Продукт-Эконом» — с Софьи Мишиной (совладелицы миноритарной доли) на
Игоря Отпущенникова. Точная дата назначения в открытых источниках не
указана (СПАРК без подписки её не показывает).

Не через `review.py`: факт из СПАРК (новый источник) не образует с уже
записанным текстом `law.struct` непрерывный кусок.

Источники — читал напрямую (WebFetch, дословные цитаты подтверждены):
https://spark-interfax.ru/primorski-krai-vladivostok/ooo-produkt-ekonom-inn-2543111589-ogrn-1172536015508-f715d0eb16334ea1ac06a23bb0135bca
https://vl.aif.ru/society/-remi-v-zaloge-dolya-torgovoy-seti-teper-u-krupneyshego-v-rossii-reteylera (дата "до")

Запуск: python3 pipeline/fix_lenta_remi_ceo_change.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gc3cb0d4d'

OLD_STRUCT = (
    'Согласно открытым источникам, контролирующую долю 67% в ООО '
    '«Продукт-Эконом» (управляет сетями супермаркетов «Реми», '
    '«РемиСити» и «Экономыч») Дмитрий Сулеев передал ООО «Лента». '
    'Оставшуюся часть поделили ООО «ВУС» (21%) Софьи и Дмитрия '
    'Мишиных, а также ООО «Меркурий» Людмилы Сулеевой (12%). Причём '
    'доли миноритариев находятся в залоге у ООО «Лента», '
    'корпоративный договор предусматривает «ограничения и условия '
    'отчуждения долей».'
)
STRUCT_ADDITION = (
    ' После закрытия сделки в ООО «Продукт-Эконом» сменился '
    'генеральный директор: пост перешёл от Софьи Мишиной (совладелицы '
    'миноритарной доли через ООО «ВУС») к Игорю Отпущенникову, '
    'сообщает СПАРК-Интерфакс; точная дата назначения в открытых '
    'источниках не указана.'
)
NEW_STRUCT = OLD_STRUCT + STRUCT_ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['law']['struct'] == OLD_STRUCT, \
        f"law.struct: неожиданное значение {deal['law']['struct']!r}"

    print(f'{CARD_ID} law.struct: += смена гендиректора '
          f'«Продукт-Эконом» после закрытия')

    if write:
        deal['law']['struct'] = NEW_STRUCT
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('ЗАПИСАНО')
    else:
        print('Сухой прогон. Запись — с --write.')


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
