# -*- coding: utf-8 -*-
"""Месячная очередь, карточка ga95b1d54 (ГАП «Ресурс»/агрофирма
«Рубеж»): дельта-поиск нашёл (1) земельный банк ГАП «Ресурс» с учётом
этой и предшествующих сделок вырос до 648 тыс. га (та же статья
Коммерсанта, но не непрерывный кусок с уже записанным текстом), и
(2) что случилось с «Рубежом» ПОСЛЕ покупки — попытка кредиторов
инициировать банкротство в мае 2026 года, которую компания назвала
необоснованной.

Не через `review.py`: (1) хоть и из уже указанного источника
(Коммерсантъ), не образует с записанным текстом непрерывный кусок;
(2) — новый источник (T-Bank/Bondomania, Cbonds).

Источники — читал напрямую (WebFetch, дословные цитаты подтверждены):
https://www.kommersant.ru/doc/7497422 (уже в src)
https://www.tbank.ru/invest/social/profile/Bondomania/7fc75b43-a4e4-447d-96c1-122c64df5e03/
https://cbonds.ru/news/3951997/ (заголовок доступен, тело — платный доступ)

Запуск: python3 pipeline/fix_gap_resurs_rubezh_context.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'ga95b1d54'

OLD_CONTEXT = (
    'В 2024 году группа выпустила 1,07 млн тонн мяса птицы в живом '
    'весе, что на 2,3% больше год к году, а также 346 тыс. тонн '
    'растительных масел и 1,92 млн тонн комбикормов. На май 2024 '
    'года ГАП «Ресурс» находилась на 13-й позиции рейтинга BEFL, '
    'контролируя 340 тыс. га земли.'
)
CONTEXT_ADDITION = (
    ' С учетом приобретения «Рубежа» и предшествующих сделок '
    'земельный банк ГАП «Ресурс» может вырасти на 308 тыс. га — до '
    '648 тыс. га. Больше года спустя, в мае 2026 года, ООО «Инвест '
    'Агро Трейд» и ООО «АгроСорос Трейд» уведомили о намерении '
    'обратиться в Арбитражный суд с заявлением о признании ООО '
    '«Агрофирма «Рубеж»» несостоятельным (банкротом) — сама '
    'агрофирма назвала эти сообщения необоснованными.'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"

    print(f'{CARD_ID} eco.context: += рост земельного банка до 648 '
          f'тыс. га и попытка банкротства цели в 2026 году')

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('ЗАПИСАНО')
    else:
        print('Сухой прогон. Запись — с --write.')


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
