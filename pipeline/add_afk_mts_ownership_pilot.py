# -*- coding: utf-8 -*-
"""П1''' (COMPANY_FINANCE_BRIEF.md, Этап 3): пилотная запись `ownership` —
АФК «Система» владеет долей в МТС. Единственная цель — проверить на живом
примере механизм «Портфель» (обратный к `holding`: у инвестора виден список
активов, а не наоборот, «МТС входит в группу АФК Система» — именно та
путаница, которой владелец просил избежать 23 августа 2026).

ПОЧЕМУ ЭТО `ownership`, А НЕ `holding`. Литмус-вопрос («работает ли „дочка"
под брендом/управлением родителя») здесь отрицателен: МТС — отдельный,
самостоятельный бренд с собственным менеджментом, не подразделение АФК.
АФК одновременно держит доли в Ozon, Сегеже и других непохожих друг на
друга компаниях — это инвестиционный портфель, не операционная группа.
`holding` для АФК не проставляется вовсе ни на одном профиле её портфеля.

ИСТОЧНИК — не пресса, а собственная страница ПАО «МТС» для инвесторов
(«Структура акционерного капитала»): 42,085% акций МТС принадлежит АФК
«Система», включая долю её дочернего ООО «Система Телеком Активы»
(11,03 п.п. внутри этих 42,085%) — на конец 2 квартала 2026 года. Это
точнее, чем встречавшаяся в прессе «эффективная доля» 49,94% (та цифра —
из новости января 2022 года, устарела на четыре с половиной года).

Запуск:
    python3 pipeline/add_afk_mts_ownership_pilot.py            # сухой прогон
    python3 pipeline/add_afk_mts_ownership_pilot.py --write
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'

INVESTOR_ID = 'gc2792a44'   # АФК «Система»
INVESTOR_NAME = 'АФК «Система»'
TARGET_ID = 'g69c88bc7'     # МТС
TARGET_NAME = 'МТС'

ENTRY = {
    'name': INVESTOR_NAME,
    'id': INVESTOR_ID,
    'share': '42,085%',
    'as_of': '2026-06',
    'source': [
        'МТС (страница для инвесторов)',
        'https://moskva.mts.ru/about/investoram-i-akcioneram/'
        'korporativnoe-upravlenie/struktura-akcionernogo-kapitala-pao-mts',
    ],
}


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    comps = data['companies']

    assert INVESTOR_ID in comps and comps[INVESTOR_ID]['name'] == INVESTOR_NAME, \
        'профиль АФК «Система» не найден или переименован'
    assert TARGET_ID in comps and comps[TARGET_ID]['name'] == TARGET_NAME, \
        'профиль МТС не найден или переименован'
    assert not comps[TARGET_ID].get('ownership'), \
        'у МТС уже есть ownership — запись добавится второй раз'

    print('Добавляем ownership на профиль «%s» (%s):' % (TARGET_NAME, TARGET_ID))
    print(json.dumps(ENTRY, ensure_ascii=False, indent=1))

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return

    comps[TARGET_ID]['ownership'] = [ENTRY]
    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('\nЗаписано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
