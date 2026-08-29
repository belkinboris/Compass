#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Карточка ОМК/Оскольский завод металлургического машиностроения несла
дату-заглушку (год 2022), хотя источник и собственные, уже дословно
перенесённые в карточку цитаты называют декабрь 2023 года.

ЧТО СЛОМАНО. Карточка `g1fa32c96» («ОМК приобрела Оскольский завод
металлургического машиностроения») стояла с `date: "2022"`. Источник
(abireg.ru) датирован «15.01.2024, 10:44» и говорит: «95,48% акций...
с 12 декабря находятся в распоряжении нового владельца» — без года в этом
самом предложении, но КОНТЕКСТ уже лежит дословно в самой карточке
(`eco.val`): «В октябре ПРОШЛОГО ГОДА стало известно, что акции завода
готовят к продаже» — «прошлый год» от даты статьи (январь 2024) это
2023-й, то есть переговоры шли с октября 2023, а не 2022. WebSearch
(tadviser.ru, interfax.ru, neftegaz.ru) независимо подтверждает: «Согласно
списку аффилированных лиц ОЗММ по состоянию на 31 декабря 2023 года,
95,48% акций предприятия принадлежали Выксунскому металлургическому
заводу» — сделка закрылась в декабре 2023 года, не в 2022-м.

САМИ ФАКТЫ (eco.share, eco.val, law.struct) уже верно и дословно перенесены
в карточку — правится только `date` (верхнеуровневое поле) и `desc`
профиля компании, где та же заглушка.

Запуск:
    python3 pipeline/fix_oskolsky_zavod_omk_date.py            # сухой прогон
    python3 pipeline/fix_oskolsky_zavod_omk_date.py --write    # записать
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'
DEAL_ID = 'g1fa32c96'
TARGET_COMPANY = 'g30a8baec'
OLD_DATE = '2022'
NEW_DATE = '2023-12-12'
OLD_DESC = 'В 2022 году его купила ОМК.'
NEW_DESC = 'В 2023 году его купила ОМК.'


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    companies = data['companies']

    deal = by_id.get(DEAL_ID)
    assert deal is not None, 'нет сделки %s' % DEAL_ID
    assert deal.get('date') == OLD_DATE, '%s: date уже не %r (сейчас %r)' % (DEAL_ID, OLD_DATE, deal.get('date'))
    assert 'с 12 декабря' in (deal.get('eco', {}).get('share') or ''), \
        'цитата про 12 декабря пропала из eco.share — проверить вручную'

    company = companies.get(TARGET_COMPANY)
    assert company is not None, 'нет профиля %s' % TARGET_COMPANY
    assert company.get('desc') == OLD_DESC, '%s: desc уже не %r' % (TARGET_COMPANY, company.get('desc'))

    print('Сделка: %s | %s' % (DEAL_ID, deal.get('title')))
    print('date: %r -> %r (источник и собственная цитата eco.val — декабрь 2023, не 2022)'
          % (OLD_DATE, NEW_DATE))
    print('Профиль %s: desc %r -> %r' % (TARGET_COMPANY, OLD_DESC, NEW_DESC))

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return

    deal['date'] = NEW_DATE
    company['desc'] = NEW_DESC

    assert by_id[DEAL_ID]['date'] == NEW_DATE
    assert companies[TARGET_COMPANY]['desc'] == NEW_DESC

    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('\nЗаписано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
