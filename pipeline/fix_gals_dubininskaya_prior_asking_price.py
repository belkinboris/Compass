# -*- coding: utf-8 -*-
"""Недельная очередь (REVISION_BRIEF, второй уровень), карточка
g0db67d5b («Галс-Девелопмент» купил советское административное здание
на Павелецкой) — найден второй источник с новой, но осторожно
формулируемой деталью: прежней ценой ЛИСТИНГА, а не ценой сделки.

Проверено лично прямым WebFetch (mirkvartir.ru, дайджест рынка
недвижимости, 26.08.2026): «Объект долгое время выставлялся на продажу
с ожидаемой ценой около 525 млн рублей». Это цена, которую ПРОСИЛ
продавец до сделки — не подтверждённая цена, по которой купил «Галс-
Девелопмент» (сама сумма сделки по-прежнему нигде не раскрыта). Родня
уже записанного урока «оценка эксперта — тоже сумма, но с пометкой»,
только здесь пометка не «по оценке», а «по цене листинга» — ещё более
явно НЕ цена сделки, и в поле `sum` она не идёт.

НЕ ВКЛЮЧЕНО: имя продавца (публичный кадастровый поиск с марта 2023
года скрывает собственников по умолчанию, платной выписки ЕГРН в этой
сессии нет); конкретные планы «Галс-Девелопмент» на участок (снос,
реконструкция, назначение) — источники называют только общую фразу
представителя компании, уже перенесённую в карточку ранее.

Запуск: python3 pipeline/fix_gals_dubininskaya_prior_asking_price.py
        python3 pipeline/fix_gals_dubininskaya_prior_asking_price.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g0db67d5b'

OLD_CONTEXT = '—'
NEW_CONTEXT = (
    'По данным обзора рынка недвижимости, здание долгое время '
    'выставлялось на продажу с ожидаемой ценой около 525 млн руб. — это '
    'прежняя цена листинга продавца, а не подтверждённая сумма сделки '
    'с «Галс-Девелопмент», которая по-прежнему не раскрыта.'
)

NEW_SRC = [
    ['MirKvartir.ru', 'https://www.mirkvartir.ru/journal/news/2026/08/26/obzor-klyuchevyh-sobytiy-rynke/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_CONTEXT

    new_src = deal['src'] + NEW_SRC

    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('\n=== src: добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
