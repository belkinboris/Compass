# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка g3d73bbfc
(«ГК ФСК купила стекольные активы Pilkington Glass Russia, ГК STiS и
активы NSG Group в России», закрыта 27 июня 2023) — продавец не был
назван, финансовый консультант продавца не был указан, масштаб сделки
(число заводов) и место сделки в истории консолидации стекольного
рынка ФСК не были раскрыты.

Проверено лично прямым WebFetch (Advance Capital,
https://advancecapital.ru/news/news/press-releases/415/):
«Продавец» — «японская NSG Group, включая стекольный завод Пилкингтон
Гласс и группу компаний СТиС»; «Покупатель» — «группа компаний ФСК»;
«Advance Capital сопровождал сделку в роли эксклюзивного финансового
консультанта продавца».

Проверено лично прямым WebFetch (fsk.ru,
https://fsk.ru/about/news/gk-fsk-rasshiryaet-prisutstvie-na-stekol-nom-rynke-i-priobretaet-pilkington-glass-russia-gk-stis-i-drugie-aktivy-nsg-group-v-rossii):
«Детали сделки стороны не разглашают» (сумма подтверждена нераскрытой
независимо, поле `sum`/`eco.sum` не менялось); итоговый портфель ГК
ФСК после сделки — «3 завода по производству листового стекла и
8 заводов по переработке стекла» (Pilkington Раменское, 8 площадок
ГК STiS — итого 11).

НЕ ВКЛЮЧЕНО (по докладу саб-агента, не проверено лично или спорно):
судьба долей РОСНАНО/ЕБРР в SP Glass до сделки 2023 года (источники
2023 года называют продавцом только NSG Group, но не объясняют, как
исчезли остальные акционеры совместного предприятия 2012 года —
вопрос оставлен открытым, не додумывается); отдельная сделка ФСК/
Sibelco (ноябрь 2023, Раменский ГОК, кварцевый песок) — это другая
сделка той же цепочки поставок, не относится к этой карточке; штраф
ФАС от 07.02.2024 — про бывшие заводы Guardian (Рязань/Ростов), не
про Раменское/STiS этой сделки.

Запуск: python3 pipeline/fix_fsk_pilkington_seller_and_advisor.py
        python3 pipeline/fix_fsk_pilkington_seller_and_advisor.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g3d73bbfc'

OLD_ADV = [
    [
        'Стороны сделки',
        'Не раскрывались',
        'Юридические консультанты в публичных источниках не раскрывались',
    ]
]
NEW_ADV = [
    [
        'Финансовый консультант продавца (NSG Group)',
        'Advance Capital',
        'Advance Capital на своём сайте называет себя эксклюзивным финансовым '
        'консультантом продавца в этой сделке. Источник: '
        'https://advancecapital.ru/news/news/press-releases/415/',
    ]
]

OLD_ECO_CONTEXT = '—'
NEW_ECO_CONTEXT = (
    'Продавец — японская NSG Group (владелец бренда Pilkington), '
    'включая завод Pilkington Glass Russia и ГК STiS. Итоговый портфель '
    'ГК ФСК после сделки — 3 завода по производству листового стекла и '
    '8 заводов по переработке (11 площадок совокупно). Это вторая '
    'крупная консолидация ФСК на стекольном рынке: в 2022 году '
    'основной акционер ФСК Владимир Воронин лично выкупил российский '
    'бизнес Guardian Glass (заводы в Рязани и Ростове-на-Дону).'
)

NEW_SRC = [
    ['Advance Capital', 'https://advancecapital.ru/news/news/press-releases/415/'],
    ['ГК ФСК', 'https://fsk.ru/about/news/gk-fsk-rasshiryaet-prisutstvie-na-stekol-nom-rynke-i-priobretaet-pilkington-glass-russia-gk-stis-i-drugie-aktivy-nsg-group-v-rossii'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['law']['adv'] == OLD_ADV
    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert 'seller' not in deal

    new_src = deal['src'] + NEW_SRC

    print('=== seller: станет ===')
    print('NSG Group')
    print('\n=== law.adv: станет ===')
    print(json.dumps(NEW_ADV, ensure_ascii=False, indent=1))
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['seller'] = 'NSG Group'
        deal['seller_src'] = 'text'
        deal['law']['adv'] = NEW_ADV
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
