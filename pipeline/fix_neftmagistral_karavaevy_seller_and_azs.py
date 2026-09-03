# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g595aca8d» («Торговый дом «Нефтьмагистраль» приобрел «Кулинарную
лавку братьев Караваевых»», закрыта 23.03.2023) — продавец не был
назван вовсе (бренд «братья Караваевы» — не настоящие люди), а планы
покупателя на кафе при АЗС не прослежены до реализации.

Проверено лично прямым WebFetch:
- Inc. Russia, https://incrussia.ru/news/neftmagistral-bratya-karavaevy/,
  27.03.2023 (перепечатка РБК, сам rbc.ru отдаёт 401): «до сделки
  владельцами были: Евгений Каценельсон и Игорь Моисеев (у обоих было
  по 50% «Селены»)»; «Компания оценена «не более чем в 100 млн руб.» по
  мнению эксперта... Условия сделки не уточняются».
- Retail.ru, https://www.retail.ru/news/kulinarnuyu-lavku-bratev-karavaevykh-kupil-vladelets-seti-azs-neftmagistral-27-marta-2023-227127/,
  27.03.2023: причины продажи со стороны прежних владельцев источник не
  называет вовсе (оба отказались от комментариев); отдельно
  подтверждает, что план «Гурманика» (60 городских кафе) — ДРУГОЙ,
  самостоятельный бренд «Нефтьмагистрали», не слитый с «Кулинарной
  лавкой» — версия о «поглощении Гурманики Караваевыми», встреченная в
  агрегированной выдаче, источником НЕ подтверждается и не вносится.
- Retail.ru, https://www.retail.ru/news/kulinarnaya-lavka-bratev-karavaevykh-budet-otkryvatsya-na-avtozapravkakh/,
  31.10.2023: «Первое полноценное кафе «Кулинарная лавка братьев
  Караваевых» строится на заправке на Дмитровском шоссе и откроется в
  следующем году»; гендиректор «Infoline-аналитики» Михаил Бурмистров —
  «открытие каждой точки кафе обойдется компании в 5–6 млн руб.»;
  совладелец «Нефтьмагистрали» Александр Ерастов — цель поднять долю
  непрофильного сегмента с 50% до 70% маржи.

НЕ ВКЛЮЧЕНО: рост сети до «более 75-80» точек и запуск франшизы к
2025-2026 годам — саб-агент нашёл эти цифры только агрегированным
WebSearch-пересказом, без прямой цитаты первоисточника; налоговое
объяснение (порог НДС в 2 млрд ₽ выручки) — это объяснение логики
рынка стрит-фуда в целом, а не персональная причина продажи ИМЕННО
Каценельсона и Моисеева, вносить как «причину сделки» было бы
натяжкой; консультанты сделки и согласование ФАС — ни один из ~12
проверенных источников их не называет.

Запуск: python3 pipeline/fix_neftmagistral_karavaevy_seller_and_azs.py
        python3 pipeline/fix_neftmagistral_karavaevy_seller_and_azs.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g595aca8d'

NEW_SELLER = 'Евгений Каценельсон и Игорь Моисеев'
NEW_SELLER_SRC = 'text'

OLD_LAW_STRUCT = '—'
NEW_LAW_STRUCT = (
    'Продажа 100% долей ООО «Селена» единой сделкой — до неё Евгений '
    'Каценельсон и Игорь Моисеев владели ими по 50% каждый. Рассрочка, '
    'опцион на выкуп или доля, сохранённая за продавцами, в источниках '
    'не упоминаются.'
)

OLD_ECO_CONTEXT = (
    'Теперь она принадлежит собственникам топливной компании '
    '«Нефтьмагистраль» — семье Ерастовых.'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' До сделки 100% ООО «Селена» принадлежали '
    'Евгению Каценельсону и Игорю Моисееву, по 50% каждому; оба '
    'отказались комментировать причины продажи. В октябре 2023 года '
    '«Нефтьмагистраль» объявила о планах открывать полноценные кафе '
    '«Кулинарная лавка братьев Караваевых» на своих заправках: первое '
    '— на Дмитровском шоссе; по оценке «Infoline-Аналитики», открытие '
    'одной точки обходится в 5-6 млн ₽; цель компании — поднять долю '
    'непрофильных продаж с 50% до 70% маржи на АЗС.'
)

NEW_SRC = [
    ['Inc. Russia', 'https://incrussia.ru/news/neftmagistral-bratya-karavaevy/'],
    ['Retail.ru', 'https://www.retail.ru/news/kulinarnuyu-lavku-bratev-karavaevykh-kupil-vladelets-seti-azs-neftmagistral-27-marta-2023-227127/'],
    ['Retail.ru', 'https://www.retail.ru/news/kulinarnaya-lavka-bratev-karavaevykh-budet-otkryvatsya-na-avtozapravkakh/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert 'seller' not in deal
    assert deal['law']['struct'] == OLD_LAW_STRUCT
    assert deal['eco']['context'] == OLD_ECO_CONTEXT

    existing_urls = {s[1] for s in deal['src']}
    add_src = [s for s in NEW_SRC if s[1] not in existing_urls]
    new_src = deal['src'] + add_src

    print('=== seller: станет ===')
    print(NEW_SELLER)
    print('\n=== law.struct: станет ===')
    print(NEW_LAW_STRUCT)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    if add_src:
        print('\n=== src: добавится ===')
        for s in add_src:
            print(s)

    if write:
        deal['seller'] = NEW_SELLER
        deal['seller_src'] = NEW_SELLER_SRC
        deal['law']['struct'] = NEW_LAW_STRUCT
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
