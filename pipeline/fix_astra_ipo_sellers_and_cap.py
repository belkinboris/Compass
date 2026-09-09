# -*- coding: utf-8 -*-
"""Месячная очередь, 9 сентября 2026 — дочитывание карточки `gb1cacbc1»
(«IPO "Группа Астра" на Московской бирже», добавлена в базу 3 августа
2026, полностью обыскана в тот же день).

Дельта-поиск (саб-агент + личная проверка) нашёл два новых факта. Личный
WebFetch (cnews.ru, 13 октября 2023) подтвердил дословно:

1) Продавцы акций и их доли. «Фролов продал 3,81% акций компании, его
   доля сократилась до 76,19%… Сивцев продал 0,95% акций компании, его
   доля сократилась до 19,0%» (до IPO — 80% и 20% соответственно);
   Фролов заработал 2,66 млрд ₽, Сивцев — 664 млн ₽. Добавлено в
   `eco.share` (стояло общей фразой о компании, без имён продавцов).

2) Капитализация по итогам размещения. «По итогам размещения
   капитализация компании составила 69,9 млрд руб.» Добавлено в
   `eco.val`.

Родня уже обработанной карточки `g4c98dcba` (SPO апреля 2024, тот же
продавец Денис Фролов) — здесь же речь о более раннем, первом IPO
(октябрь 2023), с ДРУГИМИ цифрами долей и суммой.

Запуск:
    python3 pipeline/fix_astra_ipo_sellers_and_cap.py            # сухой прогон
    python3 pipeline/fix_astra_ipo_sellers_and_cap.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

OLD_ECO_SHARE = (
    'ПАО «Группа Астра» — один из лидеров российского ИТ-рынка и '
    'ведущий производитель инфраструктурного ПО.'
)
NEW_ECO_SHARE = OLD_ECO_SHARE + (
    ' Продавцами акций выступили основатели: Денис Фролов продал 3,81% '
    'акций (доля сократилась с 80% до 76,19%, заработал 2,66 млрд ₽), '
    'Илья Сивцев продал 0,95% (доля сократилась с 20% до 19,0%, '
    'заработал 664 млн ₽).'
)

OLD_ECO_VAL = (
    'Размещение прошло по верхней границе ценового диапазона: '
    'акционеры продали 10,5 млн бумаг на 3,5 млрд ₽.'
)
NEW_ECO_VAL = OLD_ECO_VAL + (
    ' По итогам размещения капитализация компании составила 69,9 млрд ₽.'
)

NEW_SRC = ['CNews', 'https://www.cnews.ru/news/top/2023-10-13_vladeltsy_astra_linux_zarabotali']


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    d = by_id['gb1cacbc1']

    assert d['eco']['share'] == OLD_ECO_SHARE, \
        'gb1cacbc1 eco.share уже другой: %r' % (d['eco']['share'],)
    assert d['eco']['val'] == OLD_ECO_VAL, \
        'gb1cacbc1 eco.val уже другой: %r' % (d['eco']['val'],)
    urls = {s[1] for s in d['src']}
    assert NEW_SRC[1] not in urls, 'источник уже добавлен'

    print('gb1cacbc1: eco.share дополнен (продавцы Фролов/Сивцев, их '
          'доли и выручка); eco.val дополнен (капитализация 69,9 млрд '
          '₽); добавлен источник cnews.ru')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    d['eco']['share'] = NEW_ECO_SHARE
    d['eco']['val'] = NEW_ECO_VAL
    d['src'].append(NEW_SRC)

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
