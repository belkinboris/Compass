# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
gfda775ad («СМ-Клиника покупает Семейный медицинский центр ЕМС в
Солнцево», статус «Обсуждается») — сделка закрылась и уже открылась
под новым брендом, карточка об этом не знала.

Проверено лично прямым WebFetch (Vademecum,
https://vademec.ru/news/2023/07/17/sm-klinika-za-250-mln-rubley-zapustila-medtsentr-na-meste-emc-v-moskve/):
«18 июля [2023]» ГК «СМ-Клиника» открыла центр; «Инвестиции в запуск
клиники составили около 250 млн рублей»; «стал 29-м по счету
подразделением ГК»; сама сумма СДЕЛКИ (покупки актива у ЕМС) в
статье НЕ раскрывается — 250 млн ₽ это заявленные инвестиции в запуск
(ремонт, оснащение, подготовка к открытию), а не цена покупки. Та же
статья прямо подтверждает: «компания приобрела Семейный медицинский
центр (СМЦ) у Европейского медицинского центра (ЕМС)», без суммы
сделки.

Отсюда `sum`/`eco.sum` НЕ переписаны на 250 млн ₽ — это была бы
подмена одной величины другой (родня уже записанного урока «Число
может быть верным фактом и совсем не той величиной»); цифра внесена в
`eco.context` с явной оговоркой, что это инвестиции в запуск, а не
цена сделки.

НЕ ВКЛЮЧЕНО: прямая причина продажи со стороны ЕМС — ни один источник
её не называет, издание прямо пишет, что ЕМС не ответил на запрос;
рост процентных расходов ЕМС в 2022 году — финансовое давление на
ГРУППУ в целом, источник не формулирует явной причинно-следственной
связи именно с продажей этого центра, вносить как «причину сделки»
было бы натяжкой.

Запуск: python3 pipeline/fix_smklinika_ems_solntsevo_closed.py
        python3 pipeline/fix_smklinika_ems_solntsevo_closed.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gfda775ad'

OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Закрыта'

OLD_DATE = '2023-05-31'
NEW_DATE = '2023-07-18'

OLD_ECO_CONTEXT = (
    'В 2021 году выручка сети составила 15,7 млрд рублей (динамика 25% год '
    'к году). С таким показателем «СМ-Клиника» заняла четвертое место в '
    'рейтинге Аналитического центра Vademecum «ТОП200 частных '
    'многопрофильных клиник России»'
)
NEW_ECO_CONTEXT = (
    'В 2021 году выручка сети составила 15,7 млрд рублей (динамика 25% год '
    'к году). С таким показателем «СМ-Клиника» заняла четвертое место в '
    'рейтинге Аналитического центра Vademecum «ТОП200 частных '
    'многопрофильных клиник России». Центр открылся 18 июля 2023 года как '
    '29-е подразделение сети; сама сумма сделки не раскрыта, а заявленные '
    'инвестиции в запуск (ремонт и оснащение) составили около 250 млн ₽.'
)

NEW_SRC = [
    ['Vademecum', 'https://vademec.ru/news/2023/07/17/sm-klinika-za-250-mln-rubley-zapustila-medtsentr-na-meste-emc-v-moskve/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['status'] == OLD_STATUS
    assert deal['date'] == OLD_DATE
    assert deal['eco']['context'] == OLD_ECO_CONTEXT

    existing_urls = {s[1] for s in deal['src']}
    add_src = [s for s in NEW_SRC if s[1] not in existing_urls]
    new_src = deal['src'] + add_src

    print('=== status: станет ===')
    print(NEW_STATUS)
    print('\n=== date: станет ===')
    print(NEW_DATE)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    if add_src:
        print('\n=== src: добавится ===')
        for s in add_src:
            print(s)

    if write:
        deal['status'] = NEW_STATUS
        deal['date'] = NEW_DATE
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
