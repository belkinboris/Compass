# -*- coding: utf-8 -*-
"""У карточки `g41eb17f6` (IPO ПАО «Озон Фармацевтика») в `law.adv` стоял
только один юридический консультант эмитента (VERBA LEGAL). Обнаружено при
дочитывании (REVISION_BRIEF.md, поиск саб-агентом): Право.ru прямо называет
второго — «Юридическое сопровождение IPO на стороне компании совместно
осуществили VERBA LEGAL и «Линия Права»» (https://pravo.ru/company_news/255683/).

Не через `review.py`: `law.adv` — список списков, а проверка для полей без
спецобработки сравнивает плоский текст ВСЕГО значения с цитатой целиком —
структурная запись «роль | имя | примечание» так дословно никогда не совпадёт
с фразой источника (задокументировано в `pipeline/ingest/fixes/batch_b_2024.py`:
«ни один из ~3000 правок в базе не редактирует law.adv через review.py»).
Тот же факт устройства инструмента, не находка этой карточки.

Запуск: python3 pipeline/fix_ozon_farm_second_advisor.py
        python3 pipeline/fix_ozon_farm_second_advisor.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g41eb17f6'
OLD_ADV = [['Юридический консультант эмитента', 'VERBA LEGAL',
            'IPO ПАО «Озон Фармацевтика» на Мосбирже. Источник: pravo.ru']]
NEW_ADV = [['Юридический консультант эмитента', 'VERBA LEGAL',
            'IPO ПАО «Озон Фармацевтика» на Мосбирже. Источник: pravo.ru'],
           ['Юридический консультант эмитента', 'Линия Права',
            'Юридическое сопровождение IPO на стороне компании совместно '
            'осуществили VERBA LEGAL и «Линия Права». Источник: '
            'https://pravo.ru/company_news/255683/']]


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    cards = {d['id']: d for d in data['deals']}
    card = cards[CARD_ID]
    assert card['law']['adv'] == OLD_ADV, 'law.adv уже другое'
    print('ПРАВИМ %s law.adv: +второй консультант эмитента («Линия Права», '
          'подтверждён Право.ru)' % CARD_ID)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    card['law']['adv'] = NEW_ADV
    json.dump(data, open(BASE, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО')


if __name__ == '__main__':
    main(write='--write' in sys.argv[1:])
