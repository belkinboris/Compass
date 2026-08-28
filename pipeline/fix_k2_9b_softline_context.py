# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка ga857f692 (Софтлайн купил 51%
К2-9b, ИБ-компанию с опцией на полную консолидацию к 2027-2028 гг.):
`eco.context` был пустой заглушкой («—»). Дельта-поиск нашёл: чем занимается
предмет сделки (в карточке этого не было вовсе — только суммы и опция) и
что стало с ним ПОСЛЕ сделки — интеграция в направление «Инферит
Безопасность» и запуск совместного продукта. Оба факта подтверждены лично
прямым WebFetch.

1. CNews/ComNews (16-17.01.2025): К2-9b Group — «внедрением средств защиты
   информации и разработкой программных продуктов» / «комплексной системной
   интеграцией и внедрением решений в сфере информационной безопасности»,
   основана в 2019 году.
2. CNews Safe (19.03.2025): «в начале 2025 г. компания вошла в направление
   «Инферит Безопасность» российского ИТ-вендора «Инферит»» (ГК Softline);
   «Инферит Облако» и K2-9b Group совместно запустили сервис тестирования
   защищённости веб-ресурсов от DDoS-атак.

Юридические/финансовые консультанты и согласование ФАС по-прежнему не
раскрыты ни в одном найденном источнике — честная пустота, не тронуто.

Запуск: python3 pipeline/fix_k2_9b_softline_context.py
        python3 pipeline/fix_k2_9b_softline_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'ga857f692'

OLD_CONTEXT = '—'
NEW_CONTEXT = (
    'К2-9b Group занимается комплексной системной интеграцией и внедрением '
    'решений в сфере информационной безопасности, а также разработкой '
    'программных продуктов; компания основана в 2019 году (CNews, ComNews). '
    'В начале 2025 года компания вошла в направление «Инферит Безопасность» '
    'ИТ-вендора «Инферит» (входит в ГК Softline): «Инферит Облако» и K2-9b '
    'Group объявили о запуске нового сервиса по тестированию защищенности '
    'веб-ресурсов от DDoS-атак (CNews Safe, 19 марта 2025).'
)

NEW_SRC = [
    ['ComNews', 'https://www.comnews.ru/content/237202/2025-01-17/2025-w03/1008/softline-priobrel-k2-9b-group'],
    ['CNews', 'https://www.cnews.ru/news/line/2025-01-16_gk_softline_priobretaet_kontroliruyushchuyu'],
    ['CNews Safe', 'https://safe.cnews.ru/news/line/2025-03-19_inferit_oblako_gk_softline'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
