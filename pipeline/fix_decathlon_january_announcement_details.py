# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g091016a1» («Decathlon продает свой бизнес в России», объявлена
25.01.2023, статус «Обсуждается») — это самая первая, январская
новость о РЕШЕНИИ Decathlon искать покупателя, до появления конкретных
переговоров (карточка `gfb29f2c0», май 2023, FLO Retailing/Azadea
Group — сорвались) и до фактического закрытия (карточка `g60280ac0»,
октябрь 2023, ООО «АРМ»/бренд Desport). Три карточки — три РАЗНЫЕ
стадии одной саги, не дубли; сливать их не нужно, но эта, самая ранняя,
должна честно указывать, чем всё кончилось.

Проверено лично прямым WebFetch (зеркало РБК от 25.01.2023, доступный
для чтения — Ведомости, https://www.vedomosti.ru/business/news/2023/01/25/960335-rbk-decathlon-prodat-biznes):
«ритейлер намерен продать бизнес целиком», но «другой источник
рассказал, что компания готова отдельно продать свою недвижимость в
РФ» — источники расходятся в предмете сделки; финансы юрлиц за 2021
год — ООО «Октоблу» (продажи и аренда): выручка 28,6 млрд ₽, чистая
прибыль 1,5 млрд ₽; «Блу Хаус» (собственная недвижимость): выручка
948,6 млн ₽, прибыль 123,5 млн ₽; «Общая оценка российского бизнеса
Decathlon составляет 13–15 млрд рублей по мнению аналитиков» — то есть
сумма в карточке ОЦЕНКА, а не согласованная цена, пометка «(по
оценке)» была пропущена.

Родственный факт, найденный саб-агентом (Profashion,
https://profashion.ru/business/retail/decathlon-prodaet-svoy-biznes-v-rossii/,
25.01.2023, не перепроверен мной лично прямым WebFetch в этом прогоне
— тот же URL уже стоит в `src` карточки): «один из критериев при
принятии положительного решения подразумевает дисконт в размере не
менее 50% от стоимости актива» — стандартное условие правкомиссии для
продажи активов западных компаний, не специфика именно этой сделки, но
относится к согласованию.

НЕ ВКЛЮЧЕНО: полное содержание итога сделки (буквально всё это уже
подробно и полно задокументировано в `g60280ac0» — переносить его сюда
означало бы дублировать, а не дополнять; дана только короткая
перекрёстная ссылка).

Запуск: python3 pipeline/fix_decathlon_january_announcement_details.py
        python3 pipeline/fix_decathlon_january_announcement_details.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g091016a1'

OLD_SUM = '13–15 млрд ₽'
NEW_SUM = '13–15 млрд ₽ (по оценке)'

OLD_EXTRA = 'Решение Decathlon продать бизнес в России.'
NEW_EXTRA = (
    'Решение Decathlon продать бизнес в России: по данным трёх '
    'источников РБК, ретейлер намерен продать бизнес целиком, ещё один '
    'источник говорил, что покупателя ищут только для недвижимости. '
    'Юрлица группы (данные за 2021 год): ООО «Октоблу» (продажи и '
    'аренда, выручка 28,6 млрд ₽, прибыль 1,5 млрд ₽) и «Блу Хаус» '
    '(собственная недвижимость, выручка 948,6 млн ₽, прибыль 123,5 '
    'млн ₽). Сделка закрылась в октябре 2023 года продажей бизнеса ООО '
    '«АРМ» (бренд Desport) — отдельная карточка «Покупка 35 магазинов '
    'и склада Decathlon в России компанией ООО «АРМ»».'
)

OLD_LAW_APPR = 'Публично не сообщалось'
NEW_LAW_APPR = (
    'Как и для других продаж активов западных компаний, обязательное '
    'условие одобрения правительственной комиссией — дисконт не менее '
    '50% от стоимости актива.'
)

NEW_SRC = [
    ['Ведомости', 'https://www.vedomosti.ru/business/news/2023/01/25/960335-rbk-decathlon-prodat-biznes'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['sum'] == OLD_SUM
    assert deal['eco']['sum'] == OLD_SUM
    assert deal['extra'] == OLD_EXTRA
    assert deal['law']['appr'] == OLD_LAW_APPR

    existing_urls = {s[1] for s in deal['src']}
    add_src = [s for s in NEW_SRC if s[1] not in existing_urls]
    new_src = deal['src'] + add_src

    print('=== sum/eco.sum: станет ===')
    print(NEW_SUM)
    print('\n=== extra: станет ===')
    print(NEW_EXTRA)
    print('\n=== law.appr: станет ===')
    print(NEW_LAW_APPR)
    if add_src:
        print('\n=== src: добавится ===')
        for s in add_src:
            print(s)

    if write:
        deal['sum'] = NEW_SUM
        deal['eco']['sum'] = NEW_SUM
        deal['extra'] = NEW_EXTRA
        deal['law']['appr'] = NEW_LAW_APPR
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
