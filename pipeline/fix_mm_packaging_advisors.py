# -*- coding: utf-8 -*-
"""Mayr-Melnhof/MM Packaging/Granelle (`g57b3b93c`): юридические
консультанты сделки не были раскрыты заглушкой, хотя лежали в уже
привязанном источнике (cms.law, немецкий пресс-релиз, тот же документ,
из которого уже взято `law.struct`) — CMS (Вена) вела сделку целиком,
Seamless Legal (Москва) консультировала по российскому праву. `law.adv`
— список пар, не строка, `review.py` не проверяет его дословно (там нет
такого поля в FIXES ни разу за всю историю базы), поэтому правка —
разовым скриптом с ручной проверкой цитаты, как и остальные точечные
правки в этом прогоне.

Запуск: python3 pipeline/fix_mm_packaging_advisors.py           # проверка
        python3 pipeline/fix_mm_packaging_advisors.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g57b3b93c'
OLD_ADV = [
    ['Стороны сделки', 'Не раскрывались',
     'Юридические консультанты в публичных источниках не раскрывались'],
]
NEW_ADV = [
    ['Продавец (Mayr-Melnhof Group)', 'CMS',
     'Вела сделку в целом («in der gesamten Transaktion in allen '
     'rechtlichen Belangen beraten»); руководитель — партнёр Райнер '
     'Вахтер. Источник: cms.law/de/aut'],
    ['Продавец, по российскому праву', 'Seamless Legal',
     'Консультировала MM Packaging по вопросам российского права '
     '(«In russischen Rechtsfragen wurde MM Packaging von Seamless '
     'Legal in Moskau beraten»). Источник: cms.law/de/aut'],
]


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в базе' % CARD_ID
    assert card['law'].get('adv') == OLD_ADV, (
        'law.adv изменился с ожидаемого: %r' % card['law'].get('adv'))
    print('ПРАВИМ  %s: law.adv — CMS (Вена) и Seamless Legal (Москва)' % CARD_ID)
    if write:
        card['law']['adv'] = NEW_ADV
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('ЗАПИСАНО')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
