# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
g5ddac2b5 (Компания «Аптекарский» стала партнёром Central Properties
по ТРЦ «Триумф Молл» в Саратове) — план карточки (перевод объекта в
ЗПИФ «Парус» с продажей паёв розничным инвесторам) реализован
полностью, спустя два года.

Проверено лично прямым WebFetch (Smart-Lab, 27.09.2025): «26.09.2025
стартовали торги первым фондом с торговой недвижимостью от УК «Парус»»,
«На момент старта торгов капитал инвесторов составил 2,36 млрд
рублей», «на кредит банка пришлось 3,22 млрд рублей под ставку КС+3%,
срок кредита до 3 квартала 2030 года».

Проверено лично прямым WebFetch (страница фонда parus.properties/
funds/triumph, более поздний срез): «Все площади сдаются в аренду 165
арендаторам (100% заполняемость)», капитал инвесторов вырос до «5,75
млрд ₽» при «2 837» инвесторах, оценка объекта — «6 053 162 000 ₽».

НЕ ВКЛЮЧЕНО: судьба самого юрлица «Аптекарский» — по данным саб-агента
(Фонтанка, 18.06.2026, не проверено лично прямым WebFetch в этом
прогоне) эта же компания владела через ЗПИФ «Тетис капитал» тремя ТЦ
в Петербурге (доставшимися при банкротстве группы «Элис»), но к июню
2026 года само юрлицо уже недействующее — это отдельная, не
относящаяся к саратовской сделке история о структуре партнёра, а не
факт о самой карточке.

Запуск: python3 pipeline/fix_triumph_mall_saratov_parus_zpif_launched.py
        python3 pipeline/fix_triumph_mall_saratov_parus_zpif_launched.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g5ddac2b5'

OLD_EXTRA = (
    'Сбербанк осуществил роль финансового консультанта и закрыл сделку '
    'по продаже торгово-развлекательного комплекса «Триумф Молл» между '
    'Central Properties и компанией «Аптекарский». (Сбербанк (закрыл '
    'сделку по продаже объекта))'
)
NEW_EXTRA = OLD_EXTRA + (
    ' Планы перевода объекта в ЗПИФ реализованы: 26 сентября 2025 года '
    'УК «Парус управление активами» запустила торги паями фонда '
    '«Триумф» — на старте капитал инвесторов составил 2,36 млрд руб. '
    '(плюс кредит банка на 3,22 млрд руб.), позже вырос до 5,75 млрд '
    'руб. при 2837 инвесторах. Комплекс полностью заполнен — 165 '
    'арендаторов, 100% площадей в аренде.'
)

NEW_SRC = [
    ['Smart-Lab', 'https://smart-lab.ru/blog/1210266.php'],
    ['Parus Asset Management', 'https://parus.properties/funds/triumph'],
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
