# -*- coding: utf-8 -*-
"""S8 Capital/Continental (`g4577126f`): месячный дообыск нашёл судьбу
завода ПОСЛЕ сделки (переименование в «Кордиант Калугу», консолидация с
шинными активами «Кордианта», планы ребрендинга под Gislaved) и предысторию
ДО неё (простои производства 2022 года из-за санкций/логистики) — из
источников, отличных от уже занятого поля `eco.context`. `law.terms`
дополнено характеристикой юриста природы запроса в BIS (перестраховка, а
не принципиальное препятствие) — из уже процитированного источника
карточки (Коммерсантъ), не перенесённой раньше. Оба поля объединяются
дословно из разных мест одной или нескольких статей — `review.py` не
умеет такое слияние, правка разовым скриптом.

Заодно поправлен порядок значка валюты в `eco.val`: «78,0 млн €» вместо
правила CLAUDE.md «$ и € — перед числом» (уже верно в `sum`/`eco.sum`,
проверено `normalize_sum.py`, но `eco.val` в его периметр не входит).

Запуск: python3 pipeline/fix_s8_continental_followup.py           # проверка
        python3 pipeline/fix_s8_continental_followup.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g4577126f'

OLD_CONTEXT = 'Около 1100 сотрудников сохранят рабочие места.'
NEW_CONTEXT = OLD_CONTEXT + (
    ' В 2022 году шинный завод Continental в Калуге в начале марта ушел '
    'в простой, затем с апреля до конца июня возобновлял производство в '
    'целях пополнения запасов готовой продукции, но позже снова '
    'простаивал до начала августа. После сделки завод переименован в '
    'ООО «Кордиант Калуга» — новое юридическое наименование вступило в '
    'силу с 17 августа 2023 года, АО «Кордиант» получило 100% уставного '
    'капитала завода. Вместе с бывшей площадкой Continental S8 в итоге '
    'сконцентрирует мощности в почти 14 млн шин в год. Планируется, что '
    'в 2024 году на обновленном заводе Gislaved произведут 2,1 млн шин '
    'для автомобилей, что на 12% больше, чем в 2023 году. «В ближайшее '
    'время данные активы пройдут процедуру ребрендинга, при этом '
    'качество продукции продолжит соответствовать высочайшим стандартам '
    'глобального игрока шинной индустрии», — сказал управляющий '
    'директор S8 Capital Торстен Шуберт.')

OLD_TERMS = (
    'Компании для закрытия сделки ожидают одобрения американского '
    'регулятора — Бюро промышленности и безопасности (BIS) Минторга '
    'США, речь идет о лицензии на реэкспорт. Запрос на получение '
    'лицензии подала Continental.')
NEW_TERMS = OLD_TERMS + (
    ' «Возможно, подача запроса в BIS — банальная перестраховка с целью '
    'проверки сторон и аффилированных лиц на предмет присутствия в '
    'списках BIS и санкциях OFAC или на их возможную токсичность с '
    'точки зрения вторичных санкций», — считает руководитель '
    'юридической практики Grace Consulting Ltd Екатерина Орлова.')

OLD_VAL = '78,0 млн €'
NEW_VAL = '€78,0 млн'

NEW_SRCS = [
    ['Интерфакс', 'https://www.interfax.ru/business/916832'],
    ['AutoNews', 'https://www.autonews.ru/news/661671ee9a79475cc6cdb5b2'],
    ['Profile.ru', 'https://profile.ru/news/economy/holding-s8-capital-'
     'kupil-aktivy-continental-v-rossii-1327797/'],
]


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в базе' % CARD_ID
    assert card['eco'].get('context') == OLD_CONTEXT, (
        'eco.context изменился с ожидаемого: %r' % card['eco'].get('context'))
    assert card['law'].get('terms') == OLD_TERMS, (
        'law.terms изменился с ожидаемого: %r' % card['law'].get('terms'))
    assert card['eco'].get('val') == OLD_VAL, (
        'eco.val изменился с ожидаемого: %r' % card['eco'].get('val'))
    src = card.setdefault('src', [])
    print('ПРАВИМ  %s: eco.context — судьба завода до и после сделки' % CARD_ID)
    print('ПРАВИМ  %s: law.terms — характеристика запроса в BIS' % CARD_ID)
    print('ПРАВИМ  %s: eco.val — порядок значка валюты' % CARD_ID)
    if write:
        card['eco']['context'] = NEW_CONTEXT
        card['law']['terms'] = NEW_TERMS
        card['eco']['val'] = NEW_VAL
        for s in NEW_SRCS:
            if s not in src:
                src.append(s)
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('ЗАПИСАНО')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
