# -*- coding: utf-8 -*-
"""GrimTeam/«Клаустрофобия» (`ga0a49202`): месячный дообыск нашёл четыре
новых факта из ДРУГИХ источников, чем уже занятые поля — дословно
объединить с существующими цитатами `review.py` не может, правка разовым
скриптом:

- law.terms: помимо сохранения ключевых сотрудников (уже в поле),
  bg.ru называет обратную сторону — Владимир Жиганов и его менеджмент
  проекты покидают;
- law.struct: sostav.ru называет РОЛИ двух новых юрлиц (не только факт их
  учреждения, который уже в поле);
- extra: incrussia.ru называет планы новых владельцев на будущее;
- eco.context: incrussia.ru называет историю актива до сделки Ручьева —
  кем и когда основана «Клаустрофобия», за сколько её купил Ручьев в
  2019 году.

Запуск: python3 pipeline/fix_grimteam_klaustrofobiya_followup.py           # проверка
        python3 pipeline/fix_grimteam_klaustrofobiya_followup.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'ga0a49202'

OLD_TERMS = ('По словам Павла Вараксина в новой команде останутся все '
             'сотрудники, которые стояли «у истоков создания сети».')
NEW_TERMS = OLD_TERMS + ' Владимир Жиганов и его менеджмент покинут проекты.'

OLD_STRUCT = ('В конце июня 2025 года были учреждены два новых юрлица: '
              'ООО «Клаустрофобия Онлайн» и ООО «Клаустрофобия Офлайн».')
NEW_STRUCT = OLD_STRUCT + (
    ' «Клаустрофобия Онлайн» займется развитием сайта агрегатора, '
    'партнерских программ и франшизы, «Клаустрофобия Офлайн» — '
    'управлением квестами и перформансами.')

OLD_EXTRA = (
    'Сделка включала приобретение до 100% бизнеса сети «Клаустрофобия», '
    'в том числе товарных знаков, прав на программное обеспечение и '
    'социальные сети, а также переуступку прав аренды на 37 локаций и их '
    'оборудование. Сеть насчитывает 169 активных квестов и генерирует '
    'оборот около 1–1,1 млрд руб.')
NEW_EXTRA = OLD_EXTRA + (
    ' Новые владельцы планируют запускать совместные проекты с '
    'российскими стриминговыми сервисами, развлекательными компаниями и '
    'блогерами, а также возрождать популярные квесты сети.')

OLD_CONTEXT = (
    'Сделка обсуждалась около полугода. Еще в августе 2024 года стало '
    'известно о том, что «Клаустрофобия» ищет покупателя бизнеса. '
    'Источники говорили, что в 2023 году шли переговоры о продаже '
    'бизнеса «МТС Энтертеймент» (сейчас компания называется МТС Live), '
    'но стороны не сошлись по цене и сути сделки.')
NEW_CONTEXT = OLD_CONTEXT + (
    ' «Клаустрофобия» основана в 2013 году Богданом Кравцовым, Тимуром '
    'Кадыровым и Сергеем Кузнецовым. В 2019 году ее приобрел Ручьев за '
    '80 млн руб.')

NEW_SRCS = [
    ['БГ (Большой город)', 'https://bg.ru/bg/business/comm-news/'
     '28940-kvesty-sold'],
    ['Sostav.ru', 'https://www.sostav.ru/publication/cet-kvestov-'
     'klaustrofobiya-smenila-vladeltsev-77407.html'],
]


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в базе' % CARD_ID
    assert card['law'].get('terms') == OLD_TERMS, (
        'law.terms изменился с ожидаемого: %r' % card['law'].get('terms'))
    assert card['law'].get('struct') == OLD_STRUCT, (
        'law.struct изменился с ожидаемого: %r' % card['law'].get('struct'))
    assert card.get('extra') == OLD_EXTRA, (
        'extra изменился с ожидаемого: %r' % card.get('extra'))
    assert card['eco'].get('context') == OLD_CONTEXT, (
        'eco.context изменился с ожидаемого: %r' % card['eco'].get('context'))
    src = card.setdefault('src', [])
    print('ПРАВИМ  %s: law.terms — Жиганов и менеджмент покидают проекты' % CARD_ID)
    print('ПРАВИМ  %s: law.struct — роли двух новых юрлиц' % CARD_ID)
    print('ПРАВИМ  %s: extra — планы новых владельцев' % CARD_ID)
    print('ПРАВИМ  %s: eco.context — история актива до сделки Ручьева' % CARD_ID)
    if write:
        card['law']['terms'] = NEW_TERMS
        card['law']['struct'] = NEW_STRUCT
        card['extra'] = NEW_EXTRA
        card['eco']['context'] = NEW_CONTEXT
        for s in NEW_SRCS:
            if s not in src:
                src.append(s)
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('ЗАПИСАНО')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
