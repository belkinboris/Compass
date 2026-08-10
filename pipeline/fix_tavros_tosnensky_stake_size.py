# -*- coding: utf-8 -*-
"""У карточки `g1c47b363` заголовок утверждал «ГК «Таврос» купила 100% ООО
«МПК «Тосненский»»» — единственный источник карточки (уже привязанный
Коммерсантъ, доступен для скачивания) прямо пишет: «Группа «Таврос» в
конце декабря 2024 года получила 33% в ООО «МПК "Тосненский"»» — и там же
называет двух других новых совладельцев с такой же долей (АО «Виннер»,
Андрей Шутилин, 33% каждый) и Ирину Шушаначеву (1%). Ревизия по
REVISION_BRIEF нашла это не поиском НОВОГО источника, а перечитыванием уже
привязанного — там же оказалось: доля в 100% (а не 33%) была написана в
заголовке при первом импорте по невнимательности к цифре внутри статьи.

Запуск: python3 pipeline/fix_tavros_tosnensky_stake_size.py
        python3 pipeline/fix_tavros_tosnensky_stake_size.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g1c47b363'
OLD_TITLE = 'ГК «Таврос» купила 100% ООО «МПК «Тосненский»» в Ленобласти'
NEW_TITLE = 'ГК «Таврос» приобрела 33% ООО «МПК «Тосненский»» в Ленобласти'


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == CARD_ID)
    if card['title'] == NEW_TITLE:
        print('УЖЕ ПРИМЕНЕНО')
        return
    assert card['title'] == OLD_TITLE, 'title уже другой: %r' % card['title']
    print('ПРАВИМ  %s title: «100%%» -> «33%%» (источник называет именно '
          'эту долю)' % CARD_ID)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    card['title'] = NEW_TITLE
    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
