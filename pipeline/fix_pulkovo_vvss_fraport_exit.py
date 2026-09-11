# -*- coding: utf-8 -*-
"""Месячная очередь качества, 11 сентября 2026 — дочитывание карточки
`c4a6060cd» («Передача управления аэропортом Пулково от иностранных
владельцев российским юрлицам», 30 ноября 2023, weekly_researched
10 августа 2026). Карточка описывала только создание ООО «Холдинг
ВВСС» — что случилось с долями бывших иностранных совладельцев
дальше, было неизвестно.

Личный WebFetch подтвердил дословно (AKM,
https://www.akm.ru/news/fraport_prodal_25_v_kholdinge_vvss/):
«Fraport AG продал сою [так в источнике] долю (25%) в ООО «Холдинг
ВВСС» компании Orbit Aviation» — сделка зарегистрирована в ЕГРЮЛ
11 декабря 2024 года, Orbit Aviation — компания из Омана.

НЕ внесено: судьба долей остальных иностранных совладельцев (QIA,
Mubadala, Baring Vostok, РФПИ) — саб-агент не нашёл подтверждений ни
выхода, ни увеличения долей, честный отрицательный результат; точная
сумма сделки Fraport — источник её не называет.

Запуск:
    python3 pipeline/fix_pulkovo_vvss_fraport_exit.py            # сухой прогон
    python3 pipeline/fix_pulkovo_vvss_fraport_exit.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

OLD_ECO_CONTEXT = (
    'Указ президента о создании ООО «Холдинг ВВСС» и передаче '
    'управления от иностранных бенефициаров (Fraport, QIA, Mubadala, '
    'Baring Vostok, РФПИ) к российским юрлицам. Двум российским '
    'компаниям — ВВСС и «Перспективные промышленные и инфраструктурные '
    'технологии-7» — переданы права распоряжаться голосами иностранных '
    'участников.'
)
NEW_ECO_CONTEXT = OLD_ECO_CONTEXT + (
    ' Немецкая Fraport AG продала свою долю (25%) в холдинге оманской '
    'Orbit Aviation — переход доли зарегистрирован в ЕГРЮЛ 11 декабря '
    '2024 года, сумма не раскрыта.'
)

NEW_SRC = ['AKM', 'https://www.akm.ru/news/fraport_prodal_25_v_kholdinge_vvss/']


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    d = by_id['c4a6060cd']

    assert d['eco']['context'] == OLD_ECO_CONTEXT, \
        'c4a6060cd eco.context уже другой: %r' % (d['eco']['context'],)
    urls = {s[1] for s in d['src']}
    assert NEW_SRC[1] not in urls, 'источник уже добавлен: %s' % NEW_SRC[1]

    print('c4a6060cd: eco.context дополнен (Fraport продала свои 25% '
          'Orbit Aviation, декабрь 2024); добавлен источник AKM')

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
