# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка ge7ec25e7 (INGKA продала
склад в Есипово бизнесмену Роберту Узилову, ноябрь 2024): дельта-поиск
нашёл три класса фактов, все подтверждены лично прямым WebFetch —
`eco.val`, `law.appr` и `eco.context` были прочерком/заглушкой.

1. Независимая оценка рыночной стоимости комплекса — 16-18 млрд руб.
   (The Insider), сумма самой сделки по-прежнему нигде не раскрыта.
2. Согласование: сделка была одобрена правительственной комиссией по
   контролю за иностранными инвестициями (тот же источник) — раньше в
   `law.appr` стояла заглушка «Публично не сообщалось».
3. Судьба склада: Wildberries вело переговоры об аренде площадей, но в
   июле 2025 года вышло из переговоров — «часть складских зон там
   занимают высотные роботизированные системы, спроектированные
   исключительно под технологии IKEA», адаптировать их под другого
   арендатора оказалось «крайне сложно» (Ведомости).

Не через review.py: несколько фактов из НЕСКОЛЬКИХ новых источников,
описывающих три разных поля.

Запуск: python3 pipeline/fix_ingka_esipovo_warehouse_context.py
        python3 pipeline/fix_ingka_esipovo_warehouse_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'ge7ec25e7'

OLD_VAL = '—'
NEW_VAL = (
    'Рыночная стоимость комплекса в Есипово оценивается в 16–18 млрд '
    'рублей (The Insider). Сумма самой сделки не раскрывается ни в одном '
    'источнике.'
)

OLD_APPR = 'Публично не сообщалось'
NEW_APPR = (
    'По данным РБК, сделка была одобрена правительственной комиссией по '
    'контролю за иностранными инвестициями.'
)

OLD_CONTEXT = '—'
NEW_CONTEXT = (
    'После сделки маркетплейс Wildberries вёл переговоры об аренде '
    'большей части складских площадей в комплексе, но в июле 2025 года '
    'вышел из переговоров: «часть складских зон там занимают высотные '
    'роботизированные системы, спроектированные исключительно под '
    'технологии IKEA», и адаптировать их под другого арендатора оказалось '
    'крайне сложно — компании-поставщики, обслуживавшие оборудование, '
    'уже покинули Россию (Ведомости).'
)

NEW_SRC = [
    ['The Insider', 'https://theins.ru/news/276057'],
    ['Ведомости', 'https://www.vedomosti.ru/realty/articles/2025/07/17/1124848-wildberries-peredumala'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['val'] == OLD_VAL
    assert deal['law']['appr'] == OLD_APPR
    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== eco.val: станет ===')
    print(NEW_VAL)
    print('=== law.appr: станет ===')
    print(NEW_APPR)
    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['val'] = NEW_VAL
        deal['law']['appr'] = NEW_APPR
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
