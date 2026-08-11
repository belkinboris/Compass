# -*- coding: utf-8 -*-
"""Карточка g3cc2009d («Продажа российских золотодобывающих активов
Petropavlovsk PLC компании УГМК-Инвест») несла две проблемы, найденные
владельцем 11 августа:

1. `buyer` указывал на профиль `vginvest` («ВГ Инвест») — покупателя
   СОВСЕМ ДРУГОЙ сделки (MBO «Балтики», карточка `baltika`). Похоже на
   перепутанную ссылку при ручной правке: оба профиля оканчиваются на
   «инвест», разные сущности. Источники карточки (Интерфакс, mergers.ru,
   ТАСС, поиск по «УГМК-инвест получила разрешение на покупку активов
   Petropavlovsk», eastrussia.ru) называют покупателем именно
   «УГМК-Инвест» — инвестиционную структуру УГМК, а не саму группу и уж
   тем более не «ВГ Инвест». Профиля «УГМК-Инвест» в базе не было, только
   профиль материнской группы «УГМК» (g3a8fb04f, уже занят другой сделкой
   — «Сусуманзолото»). Родня уже принятого решения по Fortum/Essity/
   Polymetal (CLAUDE.md, прогон 51): иностранный/материнский бренд и его
   юрлицо-покупатель в конкретной сделке — разные профили, не сливаются.
   Новый профиль связан с УГМК через `holding`, чтобы это не потерялось.

2. `asset` начинался со строчной буквы: «золотодобывающие активы...» —
   опечатка, внесённая мной же в предыдущем прогоне
   (`fix_petropavlovsk_asset_and_duplication.py`).

Запуск: python3 pipeline/fix_petropavlovsk_buyer_and_asset_case.py           # проверка
        python3 pipeline/fix_petropavlovsk_buyer_and_asset_case.py --write   # запись
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g3cc2009d'
NEW_COMPANY_ID = 'ugmkinvest'
OLD_BUYER = 'vginvest'
OLD_ASSET = 'золотодобывающие активы Petropavlovsk PLC'
NEW_ASSET = 'Золотодобывающие активы Petropavlovsk PLC'


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    cards = {d['id']: d for d in data['deals']}
    card = cards[CARD_ID]

    assert card.get('buyer') == OLD_BUYER, (
        'ожидался buyer=%r у %s, сейчас %r — состояние изменилось'
        % (OLD_BUYER, CARD_ID, card.get('buyer')))
    assert card.get('asset') == OLD_ASSET, (
        'ожидался asset=%r у %s, сейчас %r — состояние изменилось'
        % (OLD_ASSET, CARD_ID, card.get('asset')))
    assert NEW_COMPANY_ID not in data['companies'], (
        'профиль %r уже существует — не перезаписываем' % NEW_COMPANY_ID)

    print('ПРАВИМ %s: buyer %r -> %r (новый профиль «УГМК-Инвест»), '
          'asset -> заглавная буква' % (CARD_ID, OLD_BUYER, NEW_COMPANY_ID))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    data['companies'][NEW_COMPANY_ID] = {
        'name': 'УГМК-Инвест',
        'ind': 'ГМК и добыча',
        'desc': ('Структура УГМК, выступившая покупателем в сделке по '
                 'приобретению золотодобывающих активов Petropavlovsk PLC '
                 'в 2022 году.'),
        'holding': {
            'id': 'g3a8fb04f',
            'confidence': 'disclosed',
            'source': ['Интерфакс', 'https://www.interfax-russia.ru/'
                       'far-east/news/ugmk-zakryla-sdelku-po-pokupke-'
                       'aktivov-petropavlovsk'],
        },
    }
    card['buyer'] = NEW_COMPANY_ID
    card['asset'] = NEW_ASSET

    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
