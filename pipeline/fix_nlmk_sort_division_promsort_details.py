# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g88d5e740` («НЛМК продает сортовой дивизион», закрыта 06.09.2023) —
`law.struct`, `law.appr` и `eco.target_fin` пустовали, хотя точное имя
покупателя, условия ФАС и финансы предмета названы в открытых
источниках.

Проверено лично прямым WebFetch:
- kaluga-poisk.ru, https://www.kaluga-poisk.ru/news/ekonomika/fas-razreshila-prodazhu-zavoda-nlmk-kaluga-i-vtorchermet-nlmk:
  покупатель — «ООО «Промсорт»»; одобрение ФАС от 21 сентября 2023
  года с условиями: исполнить действующие на дату сделки договоры
  поставки, в течение трёх месяцев разработать и представить принципы
  взаимодействия с потребителями, а с полугода — ежемесячно продавать
  на бирже не менее 5% арматуры от месячного объёма производства.
- revda-info.ru, https://www.revda-info.ru/2023/11/10/nlmk-ural-pereimenovan-v-promsort-ural-lisin-prodal-sortovoj-divizion-na-urale-i-v-kaluge/:
  «НЛМК-Урал» с 31 октября 2023 года переименован в АО «ПромСорт-
  Урал»; мощности — Ревда 2,2 млн т заготовки/год, Нижние Серги 1 млн
  т/год, «НЛМК-Метиз» 560 тыс. т/год; выручка «НЛМК-Урал» в 2022 году
  — 76 млрд ₽ (снижение с 95 млрд ₽), чистая прибыль — 4,7 млрд ₽
  (снижение с 15,9 млрд ₽).

НЕ ВНЕСЕНО: переименование калужского завода в «Промсорт-Калуга» (по
докладу саб-агента, не перепроверено мной лично прямым WebFetch) —
за рамками этой правки; EBITDA дивизиона 17,8 млрд ₽ за 2022 год и
финансы АО «Промсорт-Урал» за 2023-2025 годы (переход к убыткам) —
из вторичных источников/агрегаторов, не подтверждены прямым чтением
первички в этом прогоне; исполнение биржевого предписания ФАС
(TASS) — WebFetch вернул 403, не проверено.

Запуск: python3 pipeline/fix_nlmk_sort_division_promsort_details.py
        python3 pipeline/fix_nlmk_sort_division_promsort_details.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g88d5e740'

OLD_LAW_STRUCT = '—'
NEW_LAW_STRUCT = (
    'Прямой покупатель — ООО «Промсорт» (структура Евгения Зубицкого,'
    ' ПМХ). С 31 октября 2023 года «НЛМК-Урал» переименован в АО'
    ' «ПромСорт-Урал».'
)

OLD_LAW_APPR = 'Публично не сообщалось'
NEW_LAW_APPR = (
    'ФАС одобрила сделку 21 сентября 2023 года с условиями: покупатель'
    ' обязан исполнить все договоры поставки, действующие на дату'
    ' сделки, в течение трёх месяцев представить в ФАС принципы'
    ' взаимодействия с потребителями, а через полгода — ежемесячно'
    ' продавать на бирже не менее 5% арматуры от месячного объёма'
    ' производства.'
)

OLD_ECO_TARGET_FIN = '—'
NEW_ECO_TARGET_FIN = (
    'Мощности: Ревда — 2,2 млн т заготовки в год, Нижние Серги — 1 млн'
    ' т/год, «НЛМК-Метиз» — 560 тыс. т/год. Выручка «НЛМК-Урал» в 2022'
    ' году — 76 млрд ₽ (снижение с 95 млрд ₽ годом ранее), чистая'
    ' прибыль — 4,7 млрд ₽ (снижение с 15,9 млрд ₽).'
)

NEW_SRC = [
    ['kaluga-poisk.ru', 'https://www.kaluga-poisk.ru/news/ekonomika/fas-razreshila-prodazhu-zavoda-nlmk-kaluga-i-vtorchermet-nlmk'],
    ['revda-info.ru', 'https://www.revda-info.ru/2023/11/10/nlmk-ural-pereimenovan-v-promsort-ural-lisin-prodal-sortovoj-divizion-na-urale-i-v-kaluge/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['law']['struct'] == OLD_LAW_STRUCT
    assert deal['law']['appr'] == OLD_LAW_APPR
    assert deal['eco']['target_fin'] == OLD_ECO_TARGET_FIN

    existing_urls = {s[1] for s in deal['src']}
    add_src = [s for s in NEW_SRC if s[1] not in existing_urls]
    new_src = deal['src'] + add_src

    print('=== law.struct: станет ===')
    print(NEW_LAW_STRUCT)
    print('\n=== law.appr: станет ===')
    print(NEW_LAW_APPR)
    print('\n=== eco.target_fin: станет ===')
    print(NEW_ECO_TARGET_FIN)
    if add_src:
        print('\n=== src: добавится ===')
        for s in add_src:
            print(s)

    if write:
        deal['law']['struct'] = NEW_LAW_STRUCT
        deal['law']['appr'] = NEW_LAW_APPR
        deal['eco']['target_fin'] = NEW_ECO_TARGET_FIN
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
