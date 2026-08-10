# -*- coding: utf-8 -*-
"""У карточки `gcdd1b337` («МегаФон продал 25% доли в сети магазинов
Связной») `date` стоял «2022-05-12» — перепутаны день и месяц. Источник
карточки — rbc.ru/technology_and_media/05/12/2022/638b11529a79473003a808d1 —
использует адрес в формате ДД/ММ/ГГГГ: «05/12/2022» значит 5 ДЕКАБРЯ 2022
года, а не 12 мая. Независимая проверка живым поиском подтверждает
единогласно (CNews, vc.ru, Expert.ru, Forbes, ComNews, iXBT, News.ru, BFM —
все датированы 5 декабря 2022 года): «МегаФон» объявил о продаже доли в
«Связном» 5 декабря 2022 года, а не в мае.

Почему не через review.py: единственный источник карточки (RBC) в этой
сессии не отдаёт текст (401 Unauthorized) — дословной цитаты для
`date_is_supported()` взять неоткуда, хотя год не меняется (только день и
месяц).

Запуск: python3 pipeline/fix_megafon_svyaznoy_date.py
        python3 pipeline/fix_megafon_svyaznoy_date.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gcdd1b337'
OLD_DATE = '2022-05-12'
NEW_DATE = '2022-12-05'


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == CARD_ID)
    if card['date'] == NEW_DATE:
        print('УЖЕ ПРИМЕНЕНО %s' % CARD_ID)
        return
    assert card['date'] == OLD_DATE, '%s: дата уже другая' % CARD_ID
    print('ПРАВИМ  %s date: «%s» -> «%s» (перепутаны день и месяц в '
          'адресе-источнике ДД/ММ/ГГГГ)' % (CARD_ID, OLD_DATE, NEW_DATE))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    card['date'] = NEW_DATE
    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
