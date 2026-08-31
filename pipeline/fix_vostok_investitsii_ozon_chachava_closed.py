# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
g01b8b8f6 (Восток Инвестиции продаёт 27,4% акций Ozon неизвестному
покупателю) — карточка держала статус «Обсуждается» и не называла
покупателя вовсе, хотя сделка закрылась ещё в 2024 году, а конечный
владелец раскрылся публично к 2026 году.

Проверено лично прямым WebFetch (Интерфакс, 10.04.2026,
interfax.ru/business/1083246): «структуры Александра Чачавы стали
инвесторами Ozon... стало известно в июле 2025 года. Тогда Ozon
сообщал, что связанные с предпринимателем организации приобрели
компанию АО "О23", которая на тот момент владела 27,71% капитала
Ozon» — прямой юридический покупатель по сделке 2024 года — АО «О23»
(на него переоформили пакет), а не сам Чачава лично; Чачава стал
конечным бенефициаром позже, купив само «О23» (родня уже записанного
урока «Прямой юридический покупатель и конечный бенефициар — разные
роли»). «О23» с тех пор нарастила долю: «Компания АО "О23" довела долю
в капитале Ozon до 34,95%. Таким образом, "О23" стала крупнейшим
акционером группы Ozon», «доля АФК "Система" сохраняется на уровне
31,8%», «В бухотчете МКПАО "Озон" за 2025 год бенефициаром компании
указан Александр Чачава с косвенной долей владения 27,65%».

`status`: «Обсуждается» → «Закрыта» — Frank Media (18.04.2025):
«Сделка по продаже 27,64% акций... Ozon — была завершена в 2024 году».
`buyer_name` заполнен («АО "О23"», профиля юрлица в базе нет).
`title` переписан: вместо «неизвестному покупателю» — найденный прямой
покупатель. `eco.context` дополнен ростом доли «О23» и структурой
капитала на 2026 год.

НЕ ВКЛЮЧЕНО: согласования (ФАС/правкомиссия/ЦБ) — ни для сделки 2024
года (Восток Инвестиции → О23), ни для сделки 2025 года (О23 → Чачава)
ни один источник их не упоминает; `law.appr` не трогается. Точная сумма
осталась расхождением в источниках (38,2 vs 38,3 млрд ₽) — оба варианта
уже стояли в карточке, новых чисел не появилось.

Запуск: python3 pipeline/fix_vostok_investitsii_ozon_chachava_closed.py
        python3 pipeline/fix_vostok_investitsii_ozon_chachava_closed.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g01b8b8f6'

OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Закрыта'

OLD_TITLE = 'Восток Инвестиции продаёт 27,4% акций Ozon неизвестному покупателю'
NEW_TITLE = 'Восток Инвестиции продала 27,4% акций Ozon компании «О23»'

OLD_CONTEXT = '—'
NEW_CONTEXT = (
    'Прямым покупателем выступило АО «О23», на которое был переоформлен '
    'пакет. Конечным бенефициаром «О23» позже стал предприниматель '
    'Александр Чачава: «структуры Александра Чачавы стали инвесторами '
    'Ozon... стало известно в июле 2025 года» (Интерфакс, 10 апреля '
    '2026 года). С тех пор «О23» нарастила долю: «Компания АО "О23" '
    'довела долю в капитале Ozon до 34,95%. Таким образом, "О23" стала '
    'крупнейшим акционером группы Ozon», «доля АФК "Система" '
    'сохраняется на уровне 31,8%».'
)

NEW_BUYER_NAME = 'АО «О23»'

NEW_SRC = [
    ['Frank Media', 'https://frankmedia.ru/199224'],
    ['Ведомости', 'https://www.vedomosti.ru/business/articles/2025/07/28/1127313-kak-aleksandr-chachava-stal-vladeltsem-ozon'],
    ['Интерфакс', 'https://www.interfax.ru/business/1083246'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['status'] == OLD_STATUS
    assert deal['title'] == OLD_TITLE
    assert deal['eco']['context'] == OLD_CONTEXT
    assert 'buyer_name' not in deal
    assert deal['buyer'] is None

    new_src = deal['src'] + NEW_SRC

    print('=== status: станет ===')
    print(NEW_STATUS)
    print('\n=== title: станет ===')
    print(NEW_TITLE)
    print('\n=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('\n=== buyer_name: станет ===')
    print(NEW_BUYER_NAME)
    print('\n=== src: добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['status'] = NEW_STATUS
        deal['title'] = NEW_TITLE
        deal['eco']['context'] = NEW_CONTEXT
        deal['buyer_name'] = NEW_BUYER_NAME
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
