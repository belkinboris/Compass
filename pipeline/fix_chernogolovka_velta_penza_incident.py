# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g3aa57efe (ГК
«Черноголовка» купила «Вельта-Пенза»): дельта-поиск подтвердил, что сумма
сделки нигде не раскрыта (три независимых источника прямо говорят «не
раскрывается»), но нашёл важное пост-сделочное событие — 26 декабря 2025
года Роспотребнадзор приостановил деятельность предприятия после того,
как ребёнок получил ожог гортани от напитка Aloe Vera; в образцах нашли
летучие органические соединения (ацетон), одна из версий — миграция из
упаковки. Блокировка продукции через «Честный знак» росла по мере
проверки: 298 тыс. единиц на 30 декабря, 22,5 млн единиц (все партии по
четырём GTIN) — к 5 января 2026 года. Это не отдельная сделка, а
существенный факт о состоянии купленного актива, важный для читателя
карточки. Не через review.py: цитаты из ТРЁХ новых источников (rtvi.com,
kommersant.ru, ria.ru) в поле, которого раньше не было.

Запуск: python3 pipeline/fix_chernogolovka_velta_penza_incident.py
        python3 pipeline/fix_chernogolovka_velta_penza_incident.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g3aa57efe'

OLD_CONTEXT = (
    'Прежние владельцы — Юрий Колотов и Владимир Каменев (у них было по '
    '50%), которые владеют долями в пензенском производителе '
    'кондитерских изделий «Анкл ю».'
)
CONTEXT_ADDITION = (
    ' 26 декабря 2025 года Роспотребнадзор приостановил деятельность '
    'предприятия и опечатал производственные помещения после того, как '
    'ребёнок получил ожог гортани от напитка Aloe Vera — в образцах с '
    'датами изготовления с августа по декабрь 2025 года нашли летучие '
    'органические соединения (по одной из версий — миграция из '
    'упаковки). Система маркировки «Честный знак» по поручению '
    'Роспотребнадзора блокировала продукцию: 298 тыс. единиц на 30 '
    'декабря 2025 года, а к 5 января 2026 года ограничения '
    'распространились на 22,5 млн единиц — все партии по четырём GTIN.'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['rtvi.com', 'https://rtvi.com/news/rospotrebnadzor-nashel-letuchie-himikaty-v-napitke-aloe-vera-posle-ozhoga-gorla-u-rebenka/'],
    ['kommersant.ru', 'https://www.kommersant.ru/doc/8336508'],
    ['ria.ru', 'https://ria.ru/20260105/rossija-2066482196.html'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
