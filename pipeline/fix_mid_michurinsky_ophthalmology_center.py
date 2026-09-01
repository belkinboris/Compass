# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
g91b02f65 (ГК «Мать и дитя» приобрела недостроенное здание
медицинского центра на Мичуринском проспекте) — само здание уже
работает как госпиталь MD GROUP «Мичуринский», и в нём открылось новое
направление.

Проверено лично прямым WebFetch (mamadeti.ru, 12.09.2025): «Новый
центр создан для оказания высокотехнологичной медицинской помощи
пациентам с заболеваниями органов зрения и оснащён современным
оборудованием ведущих мировых производителей» — открытие Центра
офтальмологии и микрохирургии глаза в Клиническом госпитале MD GROUP
«Мичуринский».

НЕ ВКЛЮЧЕНО: объём инвестиций в центр (280 млн руб. по данным
саб-агента, источник zdrav.expert недоступен прямым WebFetch — 404,
цифра не подтверждена лично); дальнейшие сделки ГК «Мать и дитя» по
расширению сети (покупка «Эксперта», «Здравицы», «Ильинской больницы»
в 2025-2026 годах) — это отдельные, самостоятельные сделки о ДРУГИХ
активах компании, не относящиеся к зданию на Мичуринском проспекте;
заводить под них новые карточки — не задача рутины «качество».

Запуск: python3 pipeline/fix_mid_michurinsky_ophthalmology_center.py
        python3 pipeline/fix_mid_michurinsky_ophthalmology_center.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g91b02f65'

OLD_EXTRA = (
    'Завершение приобретения семиэтажного медицинского центра площадью '
    '8 755 кв. м на Мичуринском проспекте, 31 в Москве. Финансирование '
    'из собственных средств группы.'
)
NEW_EXTRA = OLD_EXTRA + (
    ' В сентябре 2025 года в здании (действующем как Клинический '
    'госпиталь MD GROUP «Мичуринский») открылся Центр офтальмологии и '
    'микрохирургии глаза.'
)

NEW_SRC = [
    ['MD Group', 'https://mamadeti.ru/news/v-moskve-otkrylsya-tsentr-oftalmologii-i-mikrokhirurgii-glaza-v-klinicheskom-gospitale-md-group-mich/'],
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
