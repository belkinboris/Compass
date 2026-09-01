# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
gd2d13f3b (Туроператор «Алеан» выкупил гостиницу Hilton Garden Inn
Moscow New Riga, закрыта 3 ноября 2023) — бренд Hilton сохранён,
финансы юрлица-собственника просели, доля перешла в личный фонд.

Проверено лично прямым WebFetch (list-org.com,
https://www.list-org.com/company/4534861): выручка ООО «Нью Рига
Резорт» упала с 544,78 млн ₽ (2024) до 488,61 млн ₽ (2025, −10%),
чистая прибыль — с 99,08 млн ₽ до 29,78 млн ₽ (−70%); учредитель —
«ЛФ "АОМ"» (личный фонд, ИНН 7730340676), сменивший физлицо-владельца.
Сайт самого «Алеана» подтверждает, что бренд Hilton Garden Inn
сохранён и по сей день: «Являясь частью международной сети отелей
Hilton, отель Hilton Garden Inn Moscow New Riga принимает участие в
программе лояльности Hilton Honals».

НЕ ВКЛЮЧЕНО: кто учредил «личный фонд «АОМ»» — открытые источники не
называют; предположение саб-агента о родстве прежнего владельца
(Андрей Уманский) с покупателем (Илья Уманский, оба с отчеством
«Геннадьевич») — совпадение отчества, не подтверждённый факт; ожидание
эксперта Tourdom.ru (февраль 2024) о возможном отказе от бренда Hilton
— это было предположение НА МОМЕНТ сделки, не сбывшееся: актуальный
сайт «Алеана» показывает обратное, поэтому в `extra` идёт факт
(бренд сохранён), а не устаревшее предположение; официальная сумма
сделки задним числом — по-прежнему не раскрыта.

Запуск: python3 pipeline/fix_alean_hilton_new_riga_ownership_and_finance.py
        python3 pipeline/fix_alean_hilton_new_riga_ownership_and_finance.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gd2d13f3b'

OLD_EXTRA = (
    'Закрытая сделка купли-продажи 100% долей ООО «Нью Рига Резорт», '
    'владеющего гостиницей. Покупатель — совладелец туроператора '
    '«Алеана» Илья Уманский. Продавец — Amtel Properties. Отель '
    'расположен в Истре, площадь 14,2 тыс. кв.м, 162 номера, категория '
    '4 звезды, управляется Hilton Worldwide.'
)
NEW_EXTRA = OLD_EXTRA + (
    ' Бренд Hilton Garden Inn сохранён и по сей день. Финансы '
    'юрлица-собственника просели: выручка упала с 544,8 до 488,6 '
    'млн ₽ (2024→2025, −10%), чистая прибыль — с 99,1 до 29,8 млн ₽ '
    '(−70%). Доля перешла из владения физлица в личный фонд.'
)

NEW_SRC = [
    ['List-org.com', 'https://www.list-org.com/company/4534861'],
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
