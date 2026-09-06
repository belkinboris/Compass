# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`gmru-kolomenskoe-peko` (ГК «Коломенский» приобрела хлебокомбинат
«Пеко», Закрыта, 27 июля 2026) — поле `seller` пустовало, хотя имена
прежних владельцев уже названы в `law.struct` этой же карточки; отдельно
нашлась конкретная сумма инвестиций в развитие завода.

Проверено ЛИЧНО прямым WebFetch:
- retail.ru/news/kolomenskoe-stanet-vladeltsem-khlebokombinata-peko-14-
  iyulya-2026-279885/: «Исак Гилядов (50% долей), Галина Фрольцова
  (25%) и Марина Цебоева (25%)» — те же три имени, что уже стоят в
  `law.struct` со ссылкой на СПАРК; более точной суммы сделки статья не
  называет (повторяет уже известную вилку 800–900 млн ₽ с учётом долга).
- new-retail.ru/novosti/retail/kolomenskiy_vykupil_khlebokombinat_peko/:
  «В развитие предприятия на первом этапе будет вложено более 1 млрд
  рублей» — конкретная цифра инвестиций, которой не было в `law.terms`
  (там только качественное описание проекта, без суммы).

Одобрение ФАС (kommersant.ru/doc/8814402, предписание на 5 лет) уже
записано в `law.appr` — повторно не вносится.

`buyer_name`/`status`/`title`/`target` карточки НЕ тронуты.

Запуск: python3 pipeline/fix_kolomenskoe_peko_seller_and_investment.py
        python3 pipeline/fix_kolomenskoe_peko_seller_and_investment.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gmru-kolomenskoe-peko'

OLD_SELLER = None
NEW_SELLER = 'Исак Гилядов, Галина Фрольцова и Марина Цебоева'

OLD_LAW_TERMS = (
    'БКХ «Коломенский» разрабатывает инвестиционный проект, который '
    'предполагает установку новых производственных линий по выпуску '
    'круглых и формовых ржано-пшеничных хлебов.'
)
NEW_LAW_TERMS = (
    OLD_LAW_TERMS + ' На первом этапе в развитие предприятия вложат '
    'более 1 млрд ₽.'
)


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal.get('seller') == OLD_SELLER
    assert deal['law']['terms'] == OLD_LAW_TERMS

    print('=== seller: станет ===')
    print(NEW_SELLER)
    print('\n=== law.terms: станет ===')
    print(NEW_LAW_TERMS)

    if write:
        deal['seller'] = NEW_SELLER
        deal['law']['terms'] = NEW_LAW_TERMS
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
