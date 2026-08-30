# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка ged395e90
(ГК «Черноголовка» купила производителя мюсли ООО «Злаки на завтрак») —
единственным источником был слабый Telegram-агрегатор @dealsma, хотя
сделку освещали настоящие издания; продавцы не были названы поимённо, а
независимая оценка суммы не была перенесена. Проверено лично прямым
WebFetch трёх источников.

`src` (заменён) — Коммерсантъ и Shopper's Media вместо @dealsma.
Дословно (Коммерсантъ, kommersant.ru/doc/6595708): «Группа компаний
«Черноголовка» приобрела компанию по производству мюсли ООО «Злаки на
завтрак» (бренды Matti и BigStar)».

`seller` (новое поле) — Дословно (Shopper's Media): «Владимир
Самохвалов (50%), Егор Осипов (33%) и Александр Красный (17%)».

`eco.val` (заполнено) — независимая оценка суммы. Дословно (Shopper's
Media, цитата управляющего партнёра Walnut Capital Артёма Моторного):
«Сумму сделки он оценивает примерно в 300 млн руб.» — записано с
атрибуцией и пометкой «(по оценке)», сама сумма сделки (`sum`/
`eco.sum`) официально не раскрыта и остаётся прочерком.

НЕ ВКЛЮЧЕНО: более ранняя история актива (юрлицо «Матти рус»,
экс-гендиректор «Нэфис косметикс» Дмитрий Харитонов) — это
предыстория бренда, а не сторона сделки 2024 года; консультанты —
не упоминаются ни в одном из пяти проверенных источников (Коммерсантъ,
Retail.ru, Shopper's Media, New-Retail.ru, vc.ru).

Запуск: python3 pipeline/fix_chernogolovka_zlaki_source_and_sellers.py
        python3 pipeline/fix_chernogolovka_zlaki_source_and_sellers.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'ged395e90'

OLD_SRC = [
    ['@dealsma (Telegram)', 'https://t.me/dealsma/4833'],
]
NEW_SRC = [
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/6595708'],
    ['Shopper’s Media', 'https://shoppers.media/news/14038_cernogolovka-kupila-proizvoditelia-miusli-i-batoncikov-matti'],
]

NEW_SELLER = 'Владимир Самохвалов (50%), Егор Осипов (33%) и Александр Красный (17%)'

OLD_VAL = '—'
NEW_VAL = (
    'Управляющий партнёр Walnut Capital Артём Моторный оценивает сумму '
    'сделки примерно в 300 млн ₽ (по оценке).'
)


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['src'] == OLD_SRC, deal['src']
    assert 'seller' not in deal, deal.get('seller')
    assert deal['eco']['val'] == OLD_VAL, deal['eco']['val']

    print('=== src: было / станет ===')
    print(OLD_SRC, '->', NEW_SRC)
    print('=== seller (новое поле) ===')
    print(NEW_SELLER)
    print('=== eco.val: было / станет ===')
    print(repr(OLD_VAL), '->', repr(NEW_VAL))

    if write:
        deal['src'] = NEW_SRC
        deal['seller'] = NEW_SELLER
        deal['seller_src'] = 'text'
        deal['eco']['val'] = NEW_VAL
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
