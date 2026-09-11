# -*- coding: utf-8 -*-
"""Месячная очередь качества, 11 сентября 2026 — дочитывание карточки
`cef2d9366» («Раздел активов Baring Vostok между российской и
зарубежной командой», 31 марта 2023, weekly_researched 10 августа
2026). Карточка описывала только сам раздел (12 компаний, включая
Ozon, $150 млн международной команде через три года) — что случилось
с долей в Ozon дальше, было неизвестно.

Личный WebFetch подтвердил дословно (Lenta.ru, 18 апреля 2025,
https://lenta.ru/news/2025/04/18/holding-vostok-investitsii-vyshel-iz-sostava-aktsionerov-ozon/):
«соглашение состоялось в 2024 году и подразумевало продажу 27,713
процента акций маркетплейса»; «Сумма сделки составила 38,3 миллиарда
рублей»; «покупателем доли в маркетплейсе должна была стать российская
структура, которая не попала под западные санкции» (имя покупателя
источник не называет).

НЕ внесено: подтверждение выплаты $150 млн международной команде —
ни один источник 2024-2026 годов не пишет об этом прямо (честный
отрицательный результат, не выдумывать); точное название компании-
покупателя доли в Ozon — не раскрыто источником.

Запуск:
    python3 pipeline/fix_baring_vostok_ozon_full_exit_2024.py            # сухой прогон
    python3 pipeline/fix_baring_vostok_ozon_full_exit_2024.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

OLD_ECO_CONTEXT = (
    'Бизнес фонда Baring Vostok разделён между российской командой '
    'партнёров и материнской компанией.'
)
NEW_ECO_CONTEXT = OLD_ECO_CONTEXT + (
    ' В 2024 году российская команда («Восток Инвестиции») полностью '
    'вышла из доли в Ozon, продав 27,713% акций маркетплейса за '
    '38,3 млрд ₽ — по условиям сделки покупателем могла стать только '
    'российская структура, не находящаяся под западными санкциями; имя '
    'покупателя не раскрыто.'
)

NEW_SRC = ['Lenta.ru', 'https://lenta.ru/news/2025/04/18/holding-vostok-investitsii-vyshel-iz-sostava-aktsionerov-ozon/']


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    d = by_id['cef2d9366']

    assert d['eco']['context'] == OLD_ECO_CONTEXT, \
        'cef2d9366 eco.context уже другой: %r' % (d['eco']['context'],)
    urls = {s[1] for s in d['src']}
    assert NEW_SRC[1] not in urls, 'источник уже добавлен: %s' % NEW_SRC[1]

    print('cef2d9366: eco.context дополнен (полный выход из доли в '
          'Ozon в 2024 году, 27,713% за 38,3 млрд ₽); добавлен '
          'источник Lenta.ru')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    d['eco']['context'] = NEW_ECO_CONTEXT
    d['src'].append(NEW_SRC)

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
