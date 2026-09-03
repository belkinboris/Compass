# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`gc9e8bb60` («Северсталь продала дистрибьютора в ЕС компании
Marcegaglia», закрыта 21.04.2023) — `eco.target_fin` и `law.adv`
пустовали/несли заглушку, хотя финансы предмета и консультант
покупателя названы в открытых источниках.

Проверено лично прямым WebFetch:
- GMK Center, https://gmk.center/en/news/marcegaglia-completed-the-acquisition-of-the-latvian-sia-severstal-distribution/:
  «The revenue of the division in 2021 amounted to €1.53 billion.»;
  «Before the war, the total capacity and throughput of enterprises
  amounted to 300 thousand tons of steel per year.»
- Официальный пресс-релиз Marcegaglia (PDF), https://www.marcegaglia.com/officialwebsite/wp-content/uploads/2023/05/21.04.2023-MARCEGAGLIA-CLOSED-PURCHASE-OF-SSD-TODAY-MARCEGAGLIA-BALTICS.pdf:
  «In the transaction, the Marcegaglia Group was followed by PWC, both
  for due diligence aspects and contractual assistance, as well as for
  all authorisation aspects.»

НЕ ВНЕСЕНО: точная выручка/реализованный оборот Marcegaglia Baltics
после сделки (найдены только целевые показатели на 2023 год — €300 млн
за 3 года и 300 рабочих мест — из интервью латвийскому инвестагентству
LIAA, не из независимой прессы, и это ПЛАН, а не факт), судьба
эскроу-счёта (снят ли режим санкций и получила ли «Северсталь» деньги)
— ни один источник этого не подтверждает. Точная дата одобрения ЕК
(5 апреля по Коммерсанту против «начала апреля» по GMK Center/пресс-
релизу Marcegaglia) — незначительное расхождение, не вносится отдельно.

Запуск: python3 pipeline/fix_severstal_marcegaglia_ssd_details.py
        python3 pipeline/fix_severstal_marcegaglia_ssd_details.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gc9e8bb60'

OLD_ECO_TARGET_FIN = '—'
NEW_ECO_TARGET_FIN = (
    'Выручка подразделения в 2021 году составила €1,53 млрд; до войны'
    ' совокупная мощность и объём переработки предприятий — 300 тыс.'
    ' тонн стали в год.'
)

OLD_LAW_ADV = [
    ['Стороны сделки', 'Не раскрывались',
     'Юридические консультанты в публичных источниках не раскрывались'],
]
NEW_LAW_ADV = [
    ['Покупатель (Marcegaglia)', 'PwC',
     'Сопровождал due diligence, контрактную часть сделки и получение'
     ' разрешений регуляторов'],
]

NEW_SRC = [
    ['GMK Center', 'https://gmk.center/en/news/marcegaglia-completed-the-acquisition-of-the-latvian-sia-severstal-distribution/'],
    ['Marcegaglia (пресс-релиз)', 'https://www.marcegaglia.com/officialwebsite/wp-content/uploads/2023/05/21.04.2023-MARCEGAGLIA-CLOSED-PURCHASE-OF-SSD-TODAY-MARCEGAGLIA-BALTICS.pdf'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['target_fin'] == OLD_ECO_TARGET_FIN
    assert deal['law']['adv'] == OLD_LAW_ADV

    existing_urls = {s[1] for s in deal['src']}
    add_src = [s for s in NEW_SRC if s[1] not in existing_urls]
    new_src = deal['src'] + add_src

    print('=== eco.target_fin: станет ===')
    print(NEW_ECO_TARGET_FIN)
    print('\n=== law.adv: станет ===')
    print(NEW_LAW_ADV)
    if add_src:
        print('\n=== src: добавится ===')
        for s in add_src:
            print(s)

    if write:
        deal['eco']['target_fin'] = NEW_ECO_TARGET_FIN
        deal['law']['adv'] = NEW_LAW_ADV
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
