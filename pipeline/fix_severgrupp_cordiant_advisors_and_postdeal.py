# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g4a751f95 (Севергрупп купила
активы производителя шин Cordiant у S8 Capital, закрыта 1 октября 2024):
`law.adv` нёс заглушку «Юридические консультанты в публичных источниках не
раскрывались» — дельта-поиск нашёл ОБОИХ консультантов поимённо, дословно
подтверждено Коммерсантом («Сделки года», 27.11.2024) и страницей команды
самой юрфирмы «Восход». Заодно дополнен `eco.context`: что стало с заводами
Cordiant ПОСЛЕ смены владельца — перезапуск завода Gislaved в Ульяновске и
покупка производителем нового завода пластиковых компонентов у A.Raymond
Group (оба факта — признак того, что новый владелец реально инвестирует в
актив, а не просто держит его). Оценка стоимости завода A.Raymond от
аналитика «Вектор Капитал» Максима Худалова НЕ перенесена в карточку: в
`eco.val` уже стоит цитата того же Худалова с оценкой ВСЕЙ сделки Cordiant,
но там он назван сотрудником «Вектор Икс» — расхождение названия фирмы
между двумя разными статьями не разрешено (не проверено, какое верно), и
чтобы не плодить на одной карточке два разных названия одной и той же
фирмы одного и того же человека, оценка стоимости завода A.Raymond в
карточку не идёт — используется только сам факт покупки.

Источники: kommersant.ru/doc/7327316 (консультанты), voskhod.legal/team
(консультант продавца, независимое подтверждение), dvizhok.su (Gislaved),
kommersant.ru/doc/7233644 (A.Raymond). Все цитаты подтверждены лично прямым
WebFetch.

Запуск: python3 pipeline/fix_severgrupp_cordiant_advisors_and_postdeal.py
        python3 pipeline/fix_severgrupp_cordiant_advisors_and_postdeal.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g4a751f95'

OLD_ADV = [
    ['Стороны сделки', 'Не раскрывались',
     'Юридические консультанты в публичных источниках не раскрывались'],
]
NEW_ADV = [
    ['Юридический консультант покупателя (Севергрупп)', 'Nextons',
     '«Юридическая фирма, сопровождающая сделку: Nextons — со стороны '
     'покупателя, «Восход» — со стороны продавца» (Коммерсантъ, '
     '«Сделки года», 27.11.2024).'],
    ['Юридический консультант продавца (S8 Capital)', '«Восход»',
     '«Команда «Восхода» представляла интересы акционеров в связи с '
     'продажей 100% акций российского производителя шин АО «Кордиант»» '
     '(voskhod.legal/team).'],
]

OLD_CONTEXT = (
    'До сделки АО «Кордиант» принадлежало топ-менеджменту. Мажоритарным '
    'акционером являлась Галина Гуринова, супруга Вадима Гуринова, '
    'основателя и председателя совета директоров ГК «Сервис-Телеком».'
)
CONTEXT_ADDITION = (
    ' После смены владельца холдинг продолжил инвестировать в производство: '
    '19 марта 2025 года официально возобновил работу завод Gislaved в '
    'Ульяновске (бывший актив Bridgestone), план на 2025 год — выпустить на '
    'этой площадке 1,2 млн шин (dvizhok.su). 15 октября 2024 года «Кордиант» '
    'также приобрёл у французской A.Raymond Group её российский бизнес — '
    'завод компонентов из пластмассы для автопрома в Нижегородской области, '
    'ООО «А.Раймонд РУС» (Коммерсантъ).'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/7327316'],
    ['Восход', 'https://www.voskhod.legal/team'],
    ['Движок', 'https://dvizhok.su/business/zavod-gislaved-v-ulyanovske-perezapusk-proizvodstva-i-planyi-na-2025-god'],
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/7233644'],
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
