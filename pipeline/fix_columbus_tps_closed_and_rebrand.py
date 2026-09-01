# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
gc96f0c6b (ТПС Недвижимость приобретает ТРЦ Columbus у структуры ГК
ПИК, статус «Обсуждается», дата «2024») — сделка закрылась ещё в 2023
году (карточка датировала её годом позже), и найден настоящий
первоисточник вместо телеграм-репоста.

Проверено лично прямым WebFetch (Ведомости, 01.06.2023): «Федеральная
антимонопольная служба (ФАС) разрешила компании "ТПС Реал Эстейт
холдинг Лимитед" приобрести 100% долей в компании "Мирс"», «Собственником
актива является основной акционер группы ПИК Сергей Гордеев»,
«Стоимость объекта консультанты оценивали в 40-45 млрд руб.» —
согласуется с уже стоящей в карточке оценкой «минимум 41 млрд руб.».

Подтверждение закрытия — проверено лично прямым WebFetch (Sostav.ru,
07.02.2025): «С 2023 года управлением объекта занимается "ТПС
Недвижимость"» — не пересказ одобрения ФАС, а факт текущего управления
спустя полтора года; тот же источник сообщает о ребрендинге центра
07.02.2025 (новый минималистичный логотип с буквой «С»).

`status`: «Обсуждается» → «Закрыта». `date`: «2024» → «2023» — точный
день перехода долей источники не называют (только дату одобрения ФАС,
1 июня 2023), поэтому в дату идёт год.

Запуск: python3 pipeline/fix_columbus_tps_closed_and_rebrand.py
        python3 pipeline/fix_columbus_tps_closed_and_rebrand.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gc96f0c6b'

OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Закрыта'

OLD_DATE = '2024'
NEW_DATE = '2023'

OLD_EXTRA = (
    'ФАС согласовал приобретение. ТПС Реал Эстейт холдинг Лимитед '
    'получит 100% долей в уставном капитале компании МИРС, которая '
    'контролирует торговый центр Columbus.'
)
NEW_EXTRA = OLD_EXTRA + (
    ' Сделка закрылась в 2023 году (ФАС одобрила её 1 июня 2023 года); '
    'по данным на февраль 2025 года объектом по-прежнему управляет '
    '«ТПС Недвижимость», в этом же месяце центр провёл ребрендинг с '
    'новым логотипом.'
)

NEW_SRC = [
    ['Ведомости', 'https://www.vedomosti.ru/realty/news/2023/06/01/978111-tps-nedvizhimost-pokupaet-krupnii-torgovii-tsentr-columbus'],
    ['Sostav.ru', 'https://www.sostav.ru/publication/torgovo-razvlekatelnyj-tsentr-columbus-73057.html'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['status'] == OLD_STATUS
    assert deal['date'] == OLD_DATE
    assert deal['extra'] == OLD_EXTRA

    new_src = deal['src'] + NEW_SRC

    print('=== status: станет ===')
    print(NEW_STATUS)
    print('\n=== date: станет ===')
    print(NEW_DATE)
    print('\n=== extra: станет ===')
    print(NEW_EXTRA)
    print('\n=== src: добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['status'] = NEW_STATUS
        deal['date'] = NEW_DATE
        deal['extra'] = NEW_EXTRA
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
