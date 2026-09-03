# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g2d075f03` («Russia Partners выставил на продажу 40% Банки.ру»,
объявлена 01.03.2023, статус «Обсуждается») — сюжет не прослежен
дальше объявления о продаже.

Проверено лично прямым WebFetch:
- Frank Media, https://frankmedia.ru/116199, 15.03.2023: «консультантом
  инвестфонда выступает «Ренессанс Капитал»»; «100% «Банки.ру» сейчас
  оцениваются в 15 млрд рублей ($198,8 [млн])» — по мнению одного из
  источников, другие называют диапазон 14-16 млрд рублей.
- Frank Media, https://frankmedia.ru/137501, 25.08.2023: «Торговую
  площадку [Московскую биржу] не устроила цена — она оказалась слишком
  высокой»; «несколько членов совета директоров» выступили против,
  считая, что «банки все меньше будут конкурировать по цене и все
  больше — по уровню сервиса»; сделка «почти развалилась из-за цены»,
  переговоры продолжались.

СТАТУС НЕ ИЗМЕНЁН: ни один источник не подтверждает ни закрытие
сделки, ни имя финального покупателя (называвшиеся кандидаты —
Московская биржа, «Яндекс», Владимир Потанин — ни один не подтверждён
как реальный покупатель; Мосбиржа прямо отказалась из-за цены в августе
2023 года). «Обсуждается» по-прежнему честно описывает состояние
сделки.

НЕ ВКЛЮЧЕНО: смена гендиректора «Банки.ру» в августе 2025 года (Роман
Халанский вместо Динары Юнусовой) — саб-агент нашёл это только по
заголовку CNews, полный текст не открывал, и это в любом случае
корпоративное событие компании, а не сама сделка по продаже доли;
структура собственности через кипрскую Banki.ru Holding Ltd — источник
только реестровые агрегаторы, не СМИ, не дословная цитата; консультант
покупателя и юридические консультанты — не названы ни в одном
источнике.

Запуск: python3 pipeline/fix_russia_partners_bankiru_status.py
        python3 pipeline/fix_russia_partners_bankiru_status.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g2d075f03'

OLD_ECO_FINADV = 'Публично не сообщалось'
NEW_ECO_FINADV = 'Продавца (Russia Partners) консультирует «Ренессанс Капитал».'

OLD_ECO_CONTEXT = '—'
NEW_ECO_CONTEXT = (
    '100% «Банки.ру» оценивались в диапазоне 14-16 млрд ₽ (около $198,8 '
    'млн по одной из оценок). В августе 2023 года Московская биржа, '
    'считавшаяся одним из кандидатов, отказалась от покупки — цена '
    'показалась ей слишком высокой, а несколько членов совета '
    'директоров усомнились в перспективности бизнеса ценового '
    'сравнения банковских услуг. Сделка к тому моменту «почти '
    'развалилась из-за цены», переговоры продолжались.'
)

NEW_SRC = [
    ['Frank Media', 'https://frankmedia.ru/116199'],
    ['Frank Media', 'https://frankmedia.ru/137501'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['finadv'] == OLD_ECO_FINADV
    assert deal['eco']['context'] == OLD_ECO_CONTEXT

    existing_urls = {s[1] for s in deal['src']}
    add_src = [s for s in NEW_SRC if s[1] not in existing_urls]
    new_src = deal['src'] + add_src

    print('=== eco.finadv: станет ===')
    print(NEW_ECO_FINADV)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    if add_src:
        print('\n=== src: добавится ===')
        for s in add_src:
            print(s)

    if write:
        deal['eco']['finadv'] = NEW_ECO_FINADV
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
