# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g739d9094` («МТС приобрела 49% долю в разработчике умных турникетов и
билетных систем «Инфоматика»», закрыта 07.03.2023) — карточка
описывала только первую, миноритарную покупку; МТС уже довела долю до
контрольной.

Проверено лично прямым WebFetch:
- Интерфакс, https://www.interfax.ru/business/997101, 11.12.2024: «ООО
  «Центр искусственного интеллекта МТС» (МТС ИИ) — нарастила долю
  владения с 49% до 55%»; «В 2023 году выручка ООО составила 574,34
  млн рублей, чистая прибыль — 32,34 млн рублей».
- Runet.news, https://runet.news/articles/67767: «Сумма сделки
  составила 50 млн руб., справедливая стоимость ранее приобретенной
  доли была оценена в 302 млн руб. То есть всего МТС вложила в данную
  компанию 352 млн руб., а вся приобретенная компания была оценена в
  640 млн руб.»; доля Тартаковского сократилась до 33,75%, ещё 11,25%
  получил Сергей Бронников; выручка 2024 года — 1,08 млрд руб., чистая
  прибыль — 176 млн руб.

НЕ ВНЕСЕНО: интеграция с VisionLabs в 2024-2025 годах и переход MTS AI
на бренд MWS AI — встретились только в агрегированной поисковой
выдаче, без подтверждения прямым чтением первоисточника; кто такой
Сергей Бронников — не выяснялось, за рамками этой карточки.
Согласование ФАС — ни один источник не упоминает.

Запуск: python3 pipeline/fix_mts_infomatika_stake_increase.py
        python3 pipeline/fix_mts_infomatika_stake_increase.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g739d9094'

OLD_LAW_STRUCT = '—'
NEW_LAW_STRUCT = (
    'В декабре 2024 года МТС ИИ увеличила долю в «Инфомате» с 49% до'
    ' 55% — доплатила 50 млн ₽ при справедливой стоимости уже'
    ' купленной доли в 302 млн ₽ (итого вложено 352 млн ₽, вся'
    ' компания оценена в 640 млн ₽). Доля Тартаковского сократилась до'
    ' 33,75%, ещё 11,25% получил Сергей Бронников.'
)

OLD_ECO_TARGET_FIN = (
    'В 2021 году выручка ООО составила 307,5 млн рублей, чистая '
    'прибыль — 8,4 млн рублей'
)
NEW_ECO_TARGET_FIN = (
    OLD_ECO_TARGET_FIN + '. В 2023 году выручка выросла до 574,34 млн'
    ' ₽, чистая прибыль — 32,34 млн ₽; в 2024 году выручка достигла'
    ' 1,08 млрд ₽, чистая прибыль — 176 млн ₽.'
)

NEW_SRC = [
    ['Интерфакс', 'https://www.interfax.ru/business/997101'],
    ['Runet.news', 'https://runet.news/articles/67767'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['law']['struct'] == OLD_LAW_STRUCT
    assert deal['eco']['target_fin'] == OLD_ECO_TARGET_FIN

    existing_urls = {s[1] for s in deal['src']}
    add_src = [s for s in NEW_SRC if s[1] not in existing_urls]
    new_src = deal['src'] + add_src

    print('=== law.struct: станет ===')
    print(NEW_LAW_STRUCT)
    print('\n=== eco.target_fin: станет ===')
    print(NEW_ECO_TARGET_FIN)
    if add_src:
        print('\n=== src: добавится ===')
        for s in add_src:
            print(s)

    if write:
        deal['law']['struct'] = NEW_LAW_STRUCT
        deal['eco']['target_fin'] = NEW_ECO_TARGET_FIN
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
