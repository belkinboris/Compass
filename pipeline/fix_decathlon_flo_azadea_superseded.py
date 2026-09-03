# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
gfb29f2c0 («FLO Retailing и Azadea Group ведут переговоры о покупке
активов Decathlon в России», май 2023, статус «Обсуждается») —
заявленные кандидаты, судя по всему, сменил другой покупатель;
карточка на реальное закрытие уже есть в базе отдельной записью.

В базе уже стоит `g60280ac0» («Покупка 35 магазинов и склада Decathlon
в России компанией ООО «АРМ»», закрыта, магазины открылись под брендом
Desport в декабре 2023) — покупатель там российский предприниматель
Вячеслав Мареев, а не FLO Retailing/Azadea Group.

Проверено лично прямым WebFetch (buybrand.ru,
https://buybrand.ru/news/decathlon-snova-otkroetsya-v-rossii-osenyu-2023-goda/):
«Кому именно достались российские активы сети, не уточняется. Однако
ранее основными претендентами на них называли турецкую компанию FLO
Retailing и ливанскую Azadea Group» — то есть независимое издание само
фиксирует смену кандидата, но БЕЗ объяснения причины и без прямого
опровержения переговоров сторонами.

Это тот же класс, что уже описан в CLAUDE.md (S8 Capital/«Аквариус»,
БКС/«Форштадт») — заявленный кандидат тихо сменился другим, ни разу не
опровергнутый напрямую. `status` НЕ меняется механически: ни один
источник не подтверждает срыва переговоров словом из закрытого списка
`STATUS_WORDS`, только отсутствие FLO/Azadea среди участников
закрытой сделки. Факт зафиксирован в `eco.context` с перекрёстной
ссылкой на реальную сделку.

НЕ ВКЛЮЧЕНО: причина смены кандидата (цена, скорость сделки,
репутационные риски) — ни один источник её не называет, не
додумывается.

Запуск: python3 pipeline/fix_decathlon_flo_azadea_superseded.py
        python3 pipeline/fix_decathlon_flo_azadea_superseded.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gfb29f2c0'

OLD_ECO_CONTEXT = '—'
NEW_ECO_CONTEXT = (
    'В итоге эти же активы Decathlon (35 магазинов и склад) в октябре '
    '2023 года были проданы не FLO Retailing/Azadea Group, а российской '
    'ООО «АРМ» (Вячеслав Мареев); магазины открылись под брендом '
    'Desport. Ни одна из сторон не подтвердила и не опровергла прямо, '
    'почему переговоры с FLO/Azadea не завершились сделкой — независимые '
    'СМИ лишь констатируют, что «кому именно достались российские '
    'активы сети, не уточняется. Однако ранее основными претендентами '
    'на них называли турецкую компанию FLO Retailing и ливанскую '
    'Azadea Group».'
)

NEW_SRC = [
    ['buybrand.ru', 'https://buybrand.ru/news/decathlon-snova-otkroetsya-v-rossii-osenyu-2023-goda/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_ECO_CONTEXT

    existing_urls = {s[1] for s in deal['src']}
    add_src = [s for s in NEW_SRC if s[1] not in existing_urls]
    new_src = deal['src'] + add_src

    print('=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    if add_src:
        print('\n=== src: добавится ===')
        for s in add_src:
            print(s)

    if write:
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
