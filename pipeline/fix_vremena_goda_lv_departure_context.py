# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g4b275e25 («Киевская
площадь» купила ТЦ «Времена года», декабрь 2024): дельта-поиск нашёл, что
отток западных люксовых брендов из ТЦ продолжился уже после смены
владельца — Louis Vuitton не продлил договор аренды (закрыл бутик на
Кутузовском в 2025 году), у бренда в России остался только один
арендованный магазин. Это прямое продолжение уже известной по началу
карточки картины (отток аудитории после ухода западных брендов в 2022
году), но новый, датированный факт после самой сделки, которого в карточке
нет. Не через review.py: цитата из НОВОГО источника (New Retail) в поле,
которое сейчас пусто (прочерк).

Запуск: python3 pipeline/fix_vremena_goda_lv_departure_context.py
        python3 pipeline/fix_vremena_goda_lv_departure_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g4b275e25'

OLD_CONTEXT = (
    'Компания «Кэпитал менеджмент», которая в конце прошлого года стала '
    'владельцем премиального торгового центра «Времена года» (65 982 кв. м) '
    'на Кутузовском проспекте, теперь выставила его на продажу.'
)
CONTEXT_ADDITION = (
    ' Отток арендаторов продолжился уже после смены владельца: Louis '
    'Vuitton не продлил договор аренды и закрыл бутик в «Временах года» в '
    '2025 году — в России у бренда остался только один арендованный '
    'магазин.'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['New Retail', 'https://new-retail.ru/novosti/retail/u_louis_vuitton_ostalsya_v_arende_odin_magazin_v_rossii/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
