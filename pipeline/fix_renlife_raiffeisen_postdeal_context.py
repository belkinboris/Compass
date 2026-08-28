# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g6520943f (Группа «Ренессанс
страхование» приобрела 100% долей СК «Райффайзен Лайф», сделка закрыта
3 октября 2024): дельта-поиск нашёл дальнейшую судьбу цели ПОСЛЕ сделки —
переименование и последующее полное присоединение к «Ренессанс Жизнь»,
с финансовыми показателями за 2024 год. Оба факта подтверждены лично прямым
WebFetch. Юридические консультанты обеих сторон (Melling, Voitishkin &
Partners — покупатель, АЛРУД — продавец) в карточке уже стояли верно —
это не новый факт, дублировать не нужно.

1. Interfax (15.04.2025): цель к этому моменту уже переименована в ООО «СК
   "Р.Лайф"», готовится присоединение к «Ренессанс Жизни»; финансовые
   показатели за 2024 год обеих компаний (Р.Лайф — сборы упали на 31,5%,
   Ренессанс Жизнь — выросли на 61,2%).
2. Raiffeisen.ru (29.07.2025): присоединение завершено 28 июля 2025 года,
   «СК «Р.Лайф»» прекратила существование как отдельное юрлицо.

`eco.context` дополнен, не заменён — старый текст описывал структуру ДО
сделки, новый — судьбу цели ПОСЛЕ.

Запуск: python3 pipeline/fix_renlife_raiffeisen_postdeal_context.py
        python3 pipeline/fix_renlife_raiffeisen_postdeal_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g6520943f'

OLD_CONTEXT = (
    'Ранее австрийская Uniqa владела 75% «Райффайзен лайф», Райффайзенбанку '
    'принадлежало 25% компании. О том, что Райффайзенбанк и Uniqa продают '
    '100% СК «Райффайзен лайф» страховой компании «Ренессанс жизнь», '
    'стороны сообщили еще в августе 2023 года.'
)
CONTEXT_ADDITION = (
    ' После сделки цель была переименована в ООО «СК «Р.Лайф»» и затем '
    'полностью присоединена к покупателю: «ООО «СК «Ренессанс Жизнь» '
    'завершило процесс присоединения ООО «СК «Р.Лайф». С 28 июля 2025 года '
    'ООО «СК «Ренессанс Жизнь» является правопреемником по всем '
    'обязательствам ООО «СК «Р.Лайф»» (Райффайзенбанк, 29 июля 2025). За '
    '2024 год, ещё до присоединения, показатели двух компаний разошлись: '
    'сборы «Ренессанс Жизнь» выросли на 61,2%, до 96,1 млрд руб., а сборы '
    '«Р.Лайф» упали на 31,5%, до 1,8 млрд руб. (Интерфакс).'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['Интерфакс', 'https://www.interfax.ru/business/1020926'],
    ['Райффайзенбанк', 'https://www.raiffeisen.ru/about/press/news/202618/'],
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
