# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка geaa4fc71 («Ароса-логистика»
купила 100% Selgros у Transgourmet, ноябрь 2024): дельта-поиск нашёл два
класса новых фактов, оба подтверждены лично прямым WebFetch.

1. Консультант сделки: Nextons сопровождала продажу — «Nextons сопровождала
   сделку по продаже австрийским акционером MCCR Beteiligungs GmbH 100%
   доли в группе компаний «Зельгрос Россия» компании «Ароса-Логистика»»
   (pravo.ru). Статья не уточняет, чью именно сторону представлял Nextons —
   записано без стороны, `law.adv` был заглушкой «Не раскрывались».
2. Судьба сети: гипермаркеты Selgros полностью закрылись к маю 2025 года,
   операционная компания «Зельгрос» — на грани банкротства (заявление
   консалтинговой Molga, более 110 исков за 2025-2026), а дистрибуторская
   «дочка» Global Foods, наоборот, растёт (выручка выросла с 14,4 до
   18,4 млрд руб. за 2025 год) — контрастная развязка судьбы двух активов
   одной сделки. `eco.context` был прочерком.

Не через review.py: факты из НЕСКОЛЬКИХ новых источников для двух разных
полей.

Запуск: python3 pipeline/fix_arosa_selgros_advisor_and_closure_context.py
        python3 pipeline/fix_arosa_selgros_advisor_and_closure_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'geaa4fc71'

OLD_ADV = [["Стороны сделки", "Не раскрывались",
            "Юридические консультанты в публичных источниках не раскрывались"]]
NEW_ADV = [["Юридический консультант", "Nextons",
            "«Nextons сопровождала сделку по продаже австрийским акционером "
            "MCCR Beteiligungs GmbH 100% доли в группе компаний «Зельгрос "
            "Россия» компании «Ароса-Логистика»» — команду возглавляли "
            "управляющий партнер Алексей Захарько и советник Ольга Попель "
            "при поддержке советника Дмитрия Микрюкова. Чью именно сторону "
            "представлял Nextons, источник не уточняет. Источник: pravo.ru"]]

OLD_CONTEXT = '—'
NEW_CONTEXT = (
    'Судьба сети после сделки оказалась контрастной для двух купленных '
    'активов. Сама сеть гипермаркетов Selgros полностью закрылась: '
    '«Год назад продуктовая сеть Selgros закрыла все гипермаркеты в '
    'России», «Последний торговый объект сети был закрыт в мае 2025 '
    'года» — операционная компания «Зельгрос» на грани банкротства '
    '(заявление подала консалтинговая компания Molga, за 2025-2026 годы '
    'против неё подано более 110 исков). При этом дистрибуторская '
    '«дочка» Global Foods, наоборот, растёт: её выручка в 2025 году '
    'выросла с 14,4 млрд до 18,4 млрд руб. (retail.ru).'
)

NEW_SRC = [
    ['Право.ru', 'https://pravo.ru/company_news/256636/'],
    ['Retail.ru', 'https://www.retail.ru/news/set-selgros-mozhet-okonchatelno-zakryt-biznes-v-rf-15-iyulya-2026-279934/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['law']['adv'] == OLD_ADV
    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== law.adv: станет ===')
    print(NEW_ADV)
    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['law']['adv'] = NEW_ADV
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
