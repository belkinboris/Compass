# -*- coding: utf-8 -*-
"""КЛВЗ «Кристалл»/«Алтайская вершина» (`g9602cce9`): месячный дообыск
нашёл базовый профиль предмета — регистрацию и род занятий ООО
«Алтайская вершина» ДО сделки, из статьи Интерфакса о самой сделке.
`eco.share` уже занято фактом об объёме продаж — дословно объединить с
цитатой из ДРУГОГО источника `review.py` не может, правка разовым
скриптом.

Запуск: python3 pipeline/fix_altayskaya_vershina_share_context.py           # проверка
        python3 pipeline/fix_altayskaya_vershina_share_context.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g9602cce9'
OLD_SHARE = ('Объем продаж водки «Алтайская Вершина» за 2022 и 2023 '
             'годы превысил 5,5 млн бутылок.')
NEW_SHARE = OLD_SHARE + (
    ' Компания, зарегистрированная в Барнауле в 2020 году, занимается '
    'оптовой торговлей напитками.')
NEW_SRC = ['Интерфакс', 'https://www.interfax.ru/business/997309']


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в базе' % CARD_ID
    assert card['eco'].get('share') == OLD_SHARE, (
        'eco.share изменился с ожидаемого: %r' % card['eco'].get('share'))
    src = card.setdefault('src', [])
    print('ПРАВИМ  %s: eco.share — регистрация и род занятий предмета до сделки' % CARD_ID)
    if write:
        card['eco']['share'] = NEW_SHARE
        if NEW_SRC not in src:
            src.append(NEW_SRC)
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('ЗАПИСАНО')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
