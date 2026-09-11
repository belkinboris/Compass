# -*- coding: utf-8 -*-
"""`gb49e3668` (Dogma купила два участка у ГК ПИК) — владелец 11 сентября
2026: «почему там не написано кто продавец? В источнике же написано, что
участки выкуплены у ГК ПИК. И почему в предмете написано «2 участка ГК
ПИК в Москве (6 га)», в этом поле не нужно писать чьи участки. Просто «2
участка в Москве (6 га)», а что ГК ПИК продавец — надо на схеме
написать.»

Два отдельных дефекта одной причины. (1) `seller`/`seller_id` не заполнены
вовсе, хотя `extra` карточки прямо, дословно называет продавца: «Dogma
купил у ГК ПИК два земельных участка» (источник — Коммерсантъ,
https://www.kommersant.ru/doc/7232560). Профиля «ГК ПИК» в базе не было —
заводится новый (родня уже записанного правила «Плашка стороны и предмет
сделки достойны собственного профиля не меньше самой стороны»). (2) Имя
профиля-предмета `g19784d41` несло имя ПРОДАВЦА внутри названия актива —
«2 участка ГК ПИК в Москве (6 га)» — та же болезнь, что уже описана в
CLAUDE.md для доли в имени («Имя компании — не место для доли»), только
здесь в имени застряла не доля, а целиком другая сторона сделки. Роль
продавца показывается отдельным полем и на схеме сторон, а не внутри
имени предмета.

Замер по всей базе (регэксп «цифра + ГК/ООО/АО/ПАО» в имени профиля) —
других таких случаев не нашлось, дефект единичный.

Запуск:
    python3 pipeline/fix_dogma_pik_seller_and_asset_name.py           # проверка
    python3 pipeline/fix_dogma_pik_seller_and_asset_name.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ROOT)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gb49e3668'
ASSET_ID = 'g19784d41'
SELLER_ID = 'gkpik'

OLD_ASSET_NAME = '2 участка ГК ПИК в Москве (6 га)'
NEW_ASSET_NAME = '2 участка в Москве (6 га)'
OLD_MATCH_KEY = '2 участка пик в москве 6 га'
NEW_MATCH_KEY = '2 участка в москве 6 га'

SELLER_PROFILE = {
    'name': 'ГК ПИК',
    'ind': 'Недвижимость',
    'desc': 'Крупнейший российский девелопер жилой недвижимости '
            '(ПАО «Группа компаний ПИК»); в 2024 году продал '
            'краснодарскому застройщику Dogma два московских участка '
            'под жильё (Гольяново, Очаково-Матвеевское).',
    'kpi': ['Профиль', 'Автоматический'],
}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    deal = next((d for d in data['deals'] if d['id'] == DEAL_ID), None)
    assert deal is not None, '%r не найдена' % DEAL_ID
    assert 'seller' not in deal and 'seller_id' not in deal, (
        'у сделки уже есть seller/seller_id — состояние изменилось: %r/%r'
        % (deal.get('seller'), deal.get('seller_id')))

    asset = data['companies'].get(ASSET_ID)
    assert asset is not None, '%r не найдена в companies' % ASSET_ID
    assert asset.get('name') == OLD_ASSET_NAME, (
        'имя профиля изменилось, ожидали %r, сейчас %r'
        % (OLD_ASSET_NAME, asset.get('name')))

    assert SELLER_ID not in data['companies'], (
        '%r уже занят — выбрать другой id' % SELLER_ID)

    mk = data.get('match_keys', {})
    assert mk.get(ASSET_ID) == [OLD_MATCH_KEY], (
        'match_keys изменились, ожидали %r, сейчас %r'
        % ([OLD_MATCH_KEY], mk.get(ASSET_ID)))

    print('ПРАВИМ: заводим профиль %r («ГК ПИК»), связываем как seller_id '
          'у %r, переименовываем %r из %r в %r'
          % (SELLER_ID, DEAL_ID, ASSET_ID, OLD_ASSET_NAME, NEW_ASSET_NAME))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    data['companies'][SELLER_ID] = SELLER_PROFILE
    data.setdefault('match_keys', {})[SELLER_ID] = ['гк пик', 'пик']

    deal['seller_id'] = SELLER_ID

    asset['name'] = NEW_ASSET_NAME
    data['match_keys'][ASSET_ID] = [NEW_MATCH_KEY]

    json.dump(data, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
