# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g3b976e82` («Goldman Sachs реструктурировал российский бизнес, продав
доли менеджменту», закрыта 30.01.2023) — структура сделки шире, чем
одна доля в HeadHunter, а дальнейшая судьба пакета не прослежена (с
явной оговоркой о неопределённости).

Проверено лично прямым WebFetch:
- Inc. Russia, https://incrussia.ru/news/goldman-russia/, 30.01.2023:
  «Основными активами Goldman Sachs в России источник назвал доли в
  Headhunter, сервисе аренды и покупки недвижимости «Циан» и операторе
  дата-центров IXcellerate Limited»; «портфель активов Goldman Sachs
  выкупил его топ-менеджмент в лице управляющего директора Максима
  Климова и управляющего директора Антона Шрейдера»; сделка «могла
  быть денежной, но с большим дисконтом».
- Lenta.ru, https://lenta.ru/news/2023/01/30/goldmanru/, 30.01.2023:
  Goldman Sachs «сократила долю в HeadHunter Group PLC... с 8,7 до 5,9
  процента»; структура покупателей владела «более 6,57 миллиона, или
  9,4 процента, акций Cian» (по состоянию на декабрь 2022).

Побочно найдено саб-агентом (НЕ включено как факт карточки — см. ниже):
две офшорные структуры покупателей, Broomfield International Limited
(Сейшелы) и Broomfield Proprietary Investments Ltd (Дубай), и попытка
проследить судьбу пакета HeadHunter в 2023-2024 годах через CNews —
сами источники (CNews, 30.06.2023 и 27.02.2024) употребляют слова
«не известно» и «возможно» о связи этих офшоров с последующими
держателями (Bluemont International, затем Леван Назаров в апреле
2024) — то есть цепочка НЕ подтверждена дословно ни одним источником,
только предполагается журналистами. Вносить её как факт нельзя.

НЕ ВКЛЮЧЕНО: офшорные названия покупателей (Broomfield) — саб-агент не
подтвердил их дословной цитатой САМОГО источника карточки (РБК), только
через DIFC-реестр и вторичные пересказы; точная сумма сделки — ни один
источник её не называет, только качественная характеристика («с
большим дисконтом»); судьба пакета после 2023 года — прямо
процитированная неопределённость самих журналистов, не факт;
согласование правкомиссии и консультанты сделки — не названы нигде.

Запуск: python3 pipeline/fix_goldman_sachs_headhunter_portfolio.py
        python3 pipeline/fix_goldman_sachs_headhunter_portfolio.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g3b976e82'

OLD_LAW_STRUCT = '—'
NEW_LAW_STRUCT = (
    'Продан не только пакет в HeadHunter, а весь портфель российских '
    'активов Goldman Sachs: доли в HeadHunter, сервисе недвижимости '
    '«Циан» и операторе дата-центров IXcellerate Limited — всё выкупил '
    'топ-менеджмент (Максим Климов и Антон Шрейдер) единой сделкой.'
)

OLD_ECO_SHARE = '—'
NEW_ECO_SHARE = (
    'Доля Goldman Sachs в HeadHunter Group PLC снизилась с 8,7% до '
    '5,9%; в «Циан» структура покупателей на декабрь 2022 года владела '
    '9,4% (6,57 млн акций).'
)

NEW_SRC = [
    ['Inc. Russia', 'https://incrussia.ru/news/goldman-russia/'],
    ['Lenta.ru', 'https://lenta.ru/news/2023/01/30/goldmanru/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['law']['struct'] == OLD_LAW_STRUCT
    assert deal['eco']['share'] == OLD_ECO_SHARE

    existing_urls = {s[1] for s in deal['src']}
    add_src = [s for s in NEW_SRC if s[1] not in existing_urls]
    new_src = deal['src'] + add_src

    print('=== law.struct: станет ===')
    print(NEW_LAW_STRUCT)
    print('\n=== eco.share: станет ===')
    print(NEW_ECO_SHARE)
    if add_src:
        print('\n=== src: добавится ===')
        for s in add_src:
            print(s)

    if write:
        deal['law']['struct'] = NEW_LAW_STRUCT
        deal['eco']['share'] = NEW_ECO_SHARE
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
