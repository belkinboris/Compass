# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка g1a6f4fec
(O1 Properties приобрела российский бизнес WeWork) — карточка не
называла конечного бенефициара покупателя и не несла именной оценки
суммы. Проверено лично прямым WebFetch трёх источников.

1) `law.struct` (дополнено) — конечный бенефициар покупателя. Дословно
(Интерфакс, 18.04.2024): «По данным аналитической системы «СПАРК-
Интерфакс», владельцем 95% компании-покупателя является Петр Букин».
Там же — обязательный ребрендинг в течение месяца: «Space 1 должна в
течение месяца поменять весь брендинг» (Sostav.ru).

2) `eco.val` (новое поле) — именная оценка суммы. Дословно (RB.ru,
источник карточки): «Сумму сделки собеседники издания назвать
затруднились»; «Если считать по модели покупки договоров аренды за три
года, то она может составить около 1,6 млрд рублей, подсчитал
генеральный директор Remain Дмитрий Клапша» — отдельная от уже стоящей
в карточке оценки (~1,5 млрд ₽, без имени), теперь с атрибуцией.

НЕ ВКЛЮЧЕНО: связь продажи российского бизнеса с банкротством WeWork
Inc. в США (ноябрь 2023) — ни один источник не формулирует прямую
причинно-следственную связь, только общий фон ($19 млрд долга при $15
млрд активов) — писать как факт нельзя; консультанты — не найдены ни в
одном из 8 проверенных источников (включая ложное срабатывание
суммаризатора поисковика, приписавшее консультацию Colliers
International — прямое чтение cre.ru/news/93473 этого не подтвердило);
судьба площадок в 2025-2026 — свежих материалов не нашлось, все детали
датированы апрелем-маем 2024.

Запуск: python3 pipeline/fix_o1_properties_wework_beneficiary_and_val.py
        python3 pipeline/fix_o1_properties_wework_beneficiary_and_val.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g1a6f4fec'

OLD_STRUCT = (
    'Space 1 создана в 2019 году компанией O1 Properties, одним из '
    'крупнейших владельцев традиционных офисов класса А в Москве.'
)
NEW_STRUCT = OLD_STRUCT + (
    ' «По данным аналитической системы «СПАРК-Интерфакс», владельцем '
    '95% компании-покупателя является Петр Букин» (Интерфакс). По '
    'условиям сделки «Space 1 должна в течение месяца поменять весь '
    'брендинг» (Sostav.ru).'
)

OLD_VAL = '—'
NEW_VAL = (
    '«Сумму сделки собеседники издания назвать затруднились. Если '
    'считать по модели покупки договоров аренды за три года, то она '
    'может составить около 1,6 млрд рублей, подсчитал генеральный '
    'директор Remain Дмитрий Клапша» (RB.ru).'
)

NEW_SRC = [
    ['Интерфакс', 'https://www.interfax.ru/business/956524'],
    ['Sostav.ru', 'https://www.sostav.ru/publication/wework-67379.html'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['law']['struct'] == OLD_STRUCT
    assert deal['eco']['val'] == OLD_VAL
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== law.struct: станет ===')
    print(NEW_STRUCT)
    print('\n=== eco.val: станет ===')
    print(NEW_VAL)
    print('\n=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['law']['struct'] = NEW_STRUCT
        deal['eco']['val'] = NEW_VAL
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
