#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""«UCL Holding» (`ge4dcbb49`) — медийное название транспортного холдинга
Владимира Лисина, а не юрлицо РФ (поиск в ЕГРЮЛ дал 0 результатов, реестр
самопроверки ИНН честно оставил decision=brand_needs_inn). Карточка
`g81b7b7e6` («UCL Holding продала Окскую судоверфь Александру Иванову»)
несла `seller_id = ge4dcbb49` — но собственный же текст карточки (`extra`)
и собственное же описание профиля `ge4dcbb49` ОБА прямо называют реального
продавца: «продажа 100% акций АО «Окская судоверфь» от АО «Волга-флот»
(входит в UCL Holding Владимира Лисина)». Тот же класс, что уже разобран
для «Арнест Юнирусь»/«Экспокап» (Этап 14, П3): бренд-платформа не может
быть стороной сделки, если известно конкретное юрлицо.

Заведён новый профиль «АО «Волга-Флот»» (ИНН 5260902190, подтверждён
кампанией самопроверки ИНН, запись `ge4dcbb49` в fns_registry.py) с
`holding.id = ge4dcbb49` — тем же приёмом, что «Арнест Менеджмент» связан
с «Арнест»: конкретное юрлицо привязано к профилю группы, а не растворено
в нём. `seller_id` карточки переставлен на новый профиль; `seller` (текст
«UCL Holding») не трогается — читатель по-прежнему видит узнаваемый бренд
в заголовке и плашке, а связанный профиль ведёт на настоящее юрлицо.

Запуск:
    python3 pipeline/fix_ucl_holding_volga_flot_seller_role.py            # сухой прогон
    python3 pipeline/fix_ucl_holding_volga_flot_seller_role.py --write    # записать
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'

DEAL_ID = 'g81b7b7e6'
OLD_SELLER_ID = 'ge4dcbb49'
NEW_PROFILE_ID = 'volga-flot'
NEW_PROFILE = {
    'name': 'АО «Волга-Флот»',
    'ind': 'Транспорт и логистика',
    'desc': (
        'Судоходная компания группы UCL Holding (Владимир Лисин); в 2023 году продала '
        '100% акций АО «Окская судоверфь» Александру Иванову.'
    ),
    'kpi': ['Профиль', 'Автоматический'],
    'holding': {
        'id': OLD_SELLER_ID,
        'confidence': 'disclosed',
        'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/6394488'],
    },
}


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    deals = {d['id']: d for d in data['deals']}
    companies = data['companies']

    deal = deals[DEAL_ID]
    assert deal['seller_id'] == OLD_SELLER_ID, 'seller_id уже не %s' % OLD_SELLER_ID
    assert deal['seller'] == 'UCL Holding'
    assert NEW_PROFILE_ID not in companies
    assert OLD_SELLER_ID in companies
    assert 'АО «Волга-флот»' in deal['extra']

    print('Проверки прошли. План:')
    print('  %s: seller_id %s -> %s (АО «Волга-Флот»)' % (DEAL_ID, OLD_SELLER_ID, NEW_PROFILE_ID))
    print('  seller (текст «UCL Holding») не меняется')
    print('  новый профиль связан holding.id -> %s' % OLD_SELLER_ID)

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return

    companies[NEW_PROFILE_ID] = NEW_PROFILE
    deal['seller_id'] = NEW_PROFILE_ID
    companies[OLD_SELLER_ID]['group'] = True

    assert companies[NEW_PROFILE_ID]['name'] == 'АО «Волга-Флот»'
    assert deals[DEAL_ID]['seller_id'] == NEW_PROFILE_ID
    assert deals[DEAL_ID]['seller'] == 'UCL Holding'
    assert companies[OLD_SELLER_ID]['group'] is True

    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('\nЗаписано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
