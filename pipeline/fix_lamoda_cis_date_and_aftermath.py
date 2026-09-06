# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g56effa09` («Яков Панченко купил бизнес Lamoda в СНГ у Global Fashion
Group», Закрыта) — дата стояла годом без месяца и дня, а судьба бизнеса
после сделки не была отражена.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- global-fashion-group.com/2022/12/12/global-fashion-group-completes-
  sale-of-lamoda/ (пресс-релиз продавца, 12.12.2022): «GFG completes the
  sale of its CIS business, Lamoda, and thereby exits Russia, Belarus
  and Kazakhstan» — сделка охватывает бизнес в России, Белоруссии и
  Казахстане (не только «СНГ» абстрактно); «€95m of proceeds (net of
  transaction costs)» плюс денежные средства в бизнесе на 30 сентября
  2022 года; покупатель — «Iakov Panchenko».
- interfax.ru/business/876593 (13.12.2022): «CEO Джери Калмис продолжит
  руководить платформой»; «У нас нет планов объединения компании с
  другими моими активами» (то есть со Stockmann); сделка структурирована
  через германскую «Eastrealty Beteiligungs und Verwaltungs GmbH»,
  принадлежащую Панченко.
- rb.ru/news/vyruchka-lamoda-po-itogam-2025-... (23.03.2026): «оборот
  (GMV) составил 213 млрд рублей (+14%), выручка — 113 млрд рублей
  (+10%)», «скорректированная EBITDA выросла до 15,5 млрд рублей
  (+27%)».

НЕ ВНЕСЕНО: перевод юрлица «Купишуз» на АО «ЛМ Холдинг» (retail.ru,
февраль 2023) и цифры дивидендов 2022–2024 годов (rb.ru) — встретились
только в сниппетах/пересказе саб-агента, не перепроверены мной лично
прямым чтением; ребрендинг марта 2025 года — источник (rb.ru) не
удалось открыть напрямую в этой сессии.

`buyer`/`status`/`title` карточки НЕ тронуты.

Запуск: python3 pipeline/fix_lamoda_cis_date_and_aftermath.py
        python3 pipeline/fix_lamoda_cis_date_and_aftermath.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g56effa09'

OLD_DATE = '2022'
NEW_DATE = '2022-12-12'

OLD_ECO_CONTEXT = '—'
NEW_ECO_CONTEXT = (
    'Сделка охватила бизнес Lamoda в России, Белоруссии и Казахстане; '
    'гендиректор Джери Калмис остался у руля, объединения со Stockmann не '
    'планировалось. К 2025 году бизнес заметно вырос: оборот (GMV) — '
    '213 млрд ₽ (+14% год к году), выручка — 113 млрд ₽ (+10%), '
    'скорректированная EBITDA — 15,5 млрд ₽ (+27%).'
)

OLD_SRC = [
    ['Forbes', 'https://www.forbes.ru/biznes/482398-vladelec-stokmanna-kupil-biznes-lamoda-v-sng'],
]
NEW_SRC = OLD_SRC + [
    ['Global Fashion Group', 'https://www.global-fashion-group.com/2022/12/12/global-fashion-group-completes-sale-of-lamoda/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['date'] == OLD_DATE
    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['src'] == OLD_SRC

    print('=== date: станет ===')
    print(NEW_DATE)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: станет ===')
    print(NEW_SRC)

    if write:
        deal['date'] = NEW_DATE
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
