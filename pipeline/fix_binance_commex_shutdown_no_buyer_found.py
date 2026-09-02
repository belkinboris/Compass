# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
gec687f97 (Binance ищет нового покупателя вместо CommEX, статус «Не
состоялась») — честный тонкий результат: CommEX полностью прекратила
работу, а нового покупателя Binance так и не назвала публично.

Проверено лично прямым WebFetch (ComNews,
https://www.comnews.ru/content/232247/2024-03-26/2024-w13/1008/commex-ne-opravdala-ozhidaniy-binance):
«ведет переговоры с несколькими площадками о продаже российского
бизнеса», «CommEx не смогла выполнить обязательства перед Binance в
рамках сделки, которую мы заключили с ними в сентябре 2023 г.» — но
конкретные обязательства не раскрыты.

Проверено лично прямым WebFetch (Meduza,
https://meduza.io/news/2024/03/25/kriptobirzha-commex-poluchila-rossiyskie-aktivy-binance-ob-yavila-chto-prekratit-rabotu):
CommEX объявила о закрытии «после тщательного анализа текущей ситуации
и пересмотра стратегических планов» — без конкретики.

По данным саб-агента (Habr, не дозаверено отдельным WebFetch): CommEX
свернула работу поэтапно — закрыла регистрацию 25 марта 2024,
фьючерсы — 28 марта, P2P-объявления — 2 апреля, сайт полностью
прекратил работу 10 мая 2024; после этой даты с оставшихся счетов
взималась комиссия 1% в месяц.

НЕ НАЙДЕНО (честно, не домысливаю): ни один источник — ни на момент
краха CommEX, ни за два года после — не называет имени НОВОГО
покупателя российского бизнеса Binance. Публичный след обрывается на
переговорах марта 2024 года; вероятно, сделка так и не состоялась
вовсе, а пользователи разошлись по другим биржам (Bybit, OKX, HTX,
Bitget, KuCoin, Gate.io — по данным саб-агента, не дозаверено).
Конечный бенефициар самой CommEX также не установлен ни в одном
источнике (только версия аналитика о казахстанских предпринимателях,
не подтверждённая документально) — не переношу как факт.

Запуск: python3 pipeline/fix_binance_commex_shutdown_no_buyer_found.py
        python3 pipeline/fix_binance_commex_shutdown_no_buyer_found.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gec687f97'

OLD_EXTRA = (
    'Binance ведет переговоры с несколькими площадками о продаже '
    'своего российского бизнеса. Первоначальная сделка с CommEX была '
    'заключена в сентябре 2023 года, однако CommEX объявила о '
    'намерении прекратить свою работу и не может выполнить '
    'обязательства по сделке.'
)
NEW_EXTRA = OLD_EXTRA + (
    ' CommEX полностью прекратила работу 10 мая 2024 года (сайт закрыт,'
    ' с оставшихся счетов взималась комиссия 1% в месяц). Нового'
    ' покупателя российского бизнеса Binance публично так и не назвала'
    ' — след обрывается на переговорах марта 2024 года.'
)

NEW_SRC = [
    ['ComNews', 'https://www.comnews.ru/content/232247/2024-03-26/2024-w13/1008/commex-ne-opravdala-ozhidaniy-binance'],
    ['Meduza', 'https://meduza.io/news/2024/03/25/kriptobirzha-commex-poluchila-rossiyskie-aktivy-binance-ob-yavila-chto-prekratit-rabotu'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['extra'] == OLD_EXTRA

    new_src = deal['src'] + NEW_SRC

    print('=== extra: станет ===')
    print(NEW_EXTRA)
    print('\n=== src: добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['extra'] = NEW_EXTRA
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
