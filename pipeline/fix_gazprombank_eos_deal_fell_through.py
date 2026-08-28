# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g3af64b90 (Газпромбанк
покупает коллекторскую компанию ЭОС у EOS Group): обязательная для
незакрытых сделок проверка статуса нашла — сделка НЕ СОСТОЯЛАСЬ. Немецкая
EOS Group официально вышла из переговоров в мае 2025 года, почти через год
после того, как карточка была добавлена. Подтверждено ДВУМЯ независимыми
изданиями лично прямым WebFetch.

1. Expert.ru (06.05.2025): «Немецкая EOS Group, владеющая крупной
   коллекторской компанией в России, отказалась продавать «дочку»
   Газпромбанку»; «иностранные акционеры ЭОС «вышли из сделки», и
   переговоры, начавшиеся осенью прошлого года, прекращены»; официальный
   комментарий компании — «EOS Group не ведет переговоров о продаже
   своего бизнеса в России».
2. Smart-lab.ru (12.05.2025), независимое подтверждение той же новости.

Прямую страницу РБК (rbc.ru/finances/06/05/2025/...) и Ведомости получить
WebFetch не удалось (401/403) — используются независимые перепечатки той
же новости с указанием даты, а не сам первоисточник.

Заодно дописаны финансовые показатели ЭОС за 2024 год (единственный
источник карточки датирован сентябрём 2024 и знает только цифры 2023
года): выручка сократилась на 11,6%, до 9,6 млрд руб., чистая прибыль —
на 7%, до 4,8 млрд руб., активы — 22,3 млрд руб. (Expert.ru).

Не через review.py: смена статуса, `law.appr` и `eco.context` меняются
одновременно по двум новым источникам.

Запуск: python3 pipeline/fix_gazprombank_eos_deal_fell_through.py
        python3 pipeline/fix_gazprombank_eos_deal_fell_through.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g3af64b90'

OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Не состоялась'

OLD_APPR = (
    'Он не уточнил, получено ли на нее разрешение специальной '
    'правительственной подкомиссии, которая курирует сделки нерезидентов '
    'из недружественных стран по продаже активов в России.'
)
NEW_APPR = (
    'Сделка не состоялась: «Немецкая EOS Group, владеющая крупной '
    'коллекторской компанией в России, отказалась продавать «дочку» '
    'Газпромбанку», «иностранные акционеры ЭОС «вышли из сделки», и '
    'переговоры, начавшиеся осенью прошлого года, прекращены» — компания '
    'подтвердила: «EOS Group не ведет переговоров о продаже своего '
    'бизнеса в России» (Expert.ru, 6 мая 2025; независимо подтверждено '
    'Smart-lab.ru, 12 мая 2025).'
)

OLD_CONTEXT = (
    '1% долей ЭОС принадлежит головной структуре немецкого холдинга EOS '
    'Holding GmbH, а остальные 99% — его «дочке», немецкой EOS '
    'International Beteiligungs-Verwaltungsgesellschaft mbH.'
)
CONTEXT_ADDITION = (
    ' За 2024 год финансовые показатели ЭОС ухудшились: выручка '
    'сократилась на 11,6%, до 9,6 млрд руб., чистая прибыль — на 7%, до '
    '4,8 млрд руб., при активах в 22,3 млрд руб. (Expert.ru).'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['Expert.ru', 'https://expert.ru/news/nemetskaya-kollektorskaya-kompaniya-otkazalas-ot-sdelki-s-gazprombankom/'],
    ['Smart-lab.ru', 'https://smart-lab.ru/blog/1153355.php'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['status'] == OLD_STATUS
    assert deal['law']['appr'] == OLD_APPR
    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== status: станет ===')
    print(NEW_STATUS)
    print('=== law.appr: станет ===')
    print(NEW_APPR)
    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['status'] = NEW_STATUS
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
