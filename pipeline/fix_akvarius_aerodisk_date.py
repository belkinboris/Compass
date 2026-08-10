# -*- coding: utf-8 -*-
"""У карточки `gadbed4b9» («Аквариус приобрел 67,8% в Аэродиск») `date`
стоял «2022-06-01» — типичная заглушка компактного импорта (первое число
месяца), да ещё и не в том году: единственный источник карточки (CNews)
сам датирован 26 июня 2023 года и прямо называет день сделки — «По данным
реестра, 21 июня 2023 г. 59,8% долей в ООО «Аеро диск» перешли ООО
«Технопарк "Электрогефест"»...» (учредитель — президент группы «Аквариус»
Владимир Степанов). Дословная дата и год в цитате не совпадают со старым
годом карточки.

Почему не через review.py: `date_is_supported()` разрешает уточнять день
только ВНУТРИ уже известного года, перенос в другой год не поддержан
намеренно (см. прецедент `fix_osnova_sviblovo_date.py`).

Запуск: python3 pipeline/fix_akvarius_aerodisk_date.py
        python3 pipeline/fix_akvarius_aerodisk_date.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gadbed4b9'
OLD_DATE = '2022-06-01'
NEW_DATE = '2023-06-21'


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == CARD_ID)
    if card['date'] == NEW_DATE:
        print('УЖЕ ПРИМЕНЕНО %s' % CARD_ID)
        return
    assert card['date'] == OLD_DATE, '%s: дата уже другая' % CARD_ID
    print('ПРАВИМ  %s date: «%s» -> «%s»' % (CARD_ID, OLD_DATE, NEW_DATE))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    card['date'] = NEW_DATE
    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
