# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
gedc0eb10 (МТС купила 85% TicketsCloud, 04.09.2023, статус «Закрыта»)
— условие полного выкупа выполнено раньше двухлетнего срока, бизнес
вырос в разы.

Проверено лично прямым WebFetch (Sostav.ru, 24.12.2024): «"МТС Лайв" —
дочерняя структура МТС — нарастила долю в сервисе Ticketscloud с 85%
до 100%» — запись в ЕГРЮЛ появилась 23 декабря 2024 года, раньше
двухлетнего срока, предусмотренного условиями сделки.

По данным саб-агента (Audit-it.ru, не дозаверено отдельным WebFetch):
выручка «Тикетсклауд» выросла с 212 млн руб. (2022) до ~559 млн руб.
(2024) и 785 млн руб. (2025, +40,5%); чистая прибыль за 2025 год — 358
млн руб. (+17,6%).

НЕ ВКЛЮЧЕНО: сумма финального выкупа доли — ни один источник её не
называет; приобретение МТС ИИ доли в казанской «Инфоматике» (умные
турникеты) — отдельная сделка другого юрлица группы МТС, не относится
к TicketsCloud напрямую; интеграция с продуктами МТС Live — саб-агент
не нашёл конкретных деталей продукта, только общую фразу о цели
сделки.

Запуск: python3 pipeline/fix_mts_ticketscloud_full_buyout.py
        python3 pipeline/fix_mts_ticketscloud_full_buyout.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gedc0eb10'

OLD_EXTRA = (
    'МТС Entertainment, дочерняя компания ПАО МТС, приобретает 85% '
    'доли в ООО «ТИКЕТСКЛАУД». Предполагается полный выкуп компании в '
    'течение двух лет при выполнении согласованных бизнес-показателей. '
    'Продавец — Егор Егерев (CEO и фаундер), инвесторы: Starta '
    'Capital, Moscow Seed Fund, Александр Бородич, Игорь Мацанюк, '
    'Богдан Яровой, 2be.lu Investment.'
)
NEW_EXTRA = OLD_EXTRA + (
    ' Условие полного выкупа выполнено раньше срока: 23 декабря 2024 '
    'года «МТС Лайв» довела долю в «Тикетсклауд» с 85% до 100%. '
    'Бизнес вырос в разы: выручка поднялась с 212 млн руб. (2022) до '
    '785 млн руб. (2025).'
)

NEW_SRC = [
    ['Sostav.ru', 'https://www.sostav.ru/publication/mts-dovela-dolyu-v-ticketscloud-do-100-72250.html'],
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
