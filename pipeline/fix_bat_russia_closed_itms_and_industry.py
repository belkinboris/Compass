# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
g95777200 («British American Tobacco продаёт российский и
беларусский бизнес консорциуму местного менеджмента», статус
«Обсуждается», 2023) — сделка давно закрыта, конечный покупатель
известен по ЕГРЮЛ, а отрасль карточки была перепутана.

Проверено лично прямым WebFetch (Интерфакс,
https://www.interfax.ru/business/920832): «Табачный концерн British
American Tobacco (BAT) закрыл сделку по продаже бизнеса в России и
Белоруссии», «Покупателем стал консорциум, возглавляемый местным
менеджментом», «после совершения сделки активы будут переименованы в
ITMS Group», «выручка ООО «Международные услуги по маркетингу табака»
(МУМТ, структура BAT в РФ, которая занималась оптовыми продажами) в
2022 году составила 247,2 млрд рублей против 225,4 млрд рублей в 2021
году, чистая прибыль - 12,1 млрд рублей против 6,2 млрд рублей
соответственно».

Проверено лично прямым WebFetch (Интерфакс,
https://www.interfax.ru/business/930213): «По данным ЕГРЮЛ, АО
"БАТ-СПб" и АО "МУМТ" перешли BFI Holding из Абу-Даби», владельцы —
«Фарук Енер, Олег Барвин, Елена Заварзина, Андрей Осаволюк и Сергей
Кудинов» («Енер был гендиректором BAT по России, Турции, Кавказу,
Центральной Азии и Белоруссии, Барвин возглавлял департамент по
правовым вопросам»); доли рынка 2022 года — BAT 23,6%, JTI 35,6%,
Philip Morris 31,1%; «Бывший менеджмент BAT контролирует ITMS, что
позволит BAT вернуться к владению активами при стабилизации ситуации»
(источник «Ъ» в отрасли — не подтверждённое условие сделки, а
предположение источника, поэтому подано в `law.terms` с явной
оговоркой «по мнению источника», а не как факт).

Проверено лично прямым WebFetch (Коммерсантъ,
https://www.kommersant.ru/doc/6212859): «завершили продажу наших
российских и белорусских предприятий» (пресс-релиз BAT), «BAT Russia
перейдут предприятия British American Tobacco в России и Белоруссии
под названием ITMS Group».

ОТРАСЛЬ БЫЛА ПЕРЕПУТАНА: `ind` карточки стоял «Химия и удобрения» —
для табачной компании это явная ошибка (сравнение с соседней карточкой
Philip Morris/Megapolis Distribution, `g4f4dc9b5`, где та же отрасль
рынка верно размечена как «Пищепром и напитки»). Меняется на
«Пищепром и напитки» для единообразия с уже принятой в базе разметкой
табачного бизнеса; тот же дефект нашёлся и у профиля покупателя
(`gc551a7f5`, «консорциум российских инвесторов и местного
менеджмента») — тоже «Химия и удобрения», тоже правится. Заодно
описание профиля покупателя дополнено найденным именем актива после
сделки (ITMS Group) и конечным юрлицом-держателем (BFI Holding).

НЕ ВКЛЮЧЕНО: рост выручки ITMS Group в 2024 году на 31% до 94,4 млрд ₽
— встретилось только в пересказе поисковика (tadviser.ru), прямую
страницу открыть не удалось (404), дословной цитаты нет; юридический
консультант сделки — ни один источник его не называет.

Запуск: python3 pipeline/fix_bat_russia_closed_itms_and_industry.py
        python3 pipeline/fix_bat_russia_closed_itms_and_industry.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g95777200'

OLD_IND = 'Химия и удобрения'
NEW_IND = 'Пищепром и напитки'

OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Закрыта'

OLD_ECO_CONTEXT = (
    'Соглашение предполагает сохранение трудовых условий для '
    'сотрудников компании в течение двух лет после закрытия сделки.'
)
NEW_ECO_CONTEXT = OLD_ECO_CONTEXT + (
    ' После закрытия сделки активы переименованы в ITMS Group '
    '(International Tobacco Marketing Services Group). В 2022 году '
    'доля BAT на российском табачном рынке составляла 23,6% (у JTI — '
    '35,6%, у Philip Morris — 31,1%).'
)

OLD_ECO_TARGET_FIN = '—'
NEW_ECO_TARGET_FIN = (
    'ООО «Международные услуги по маркетингу табака» (МУМТ, структура '
    'BAT в РФ, оптовые продажи): выручка за 2022 год — 247,2 млрд ₽ '
    '(225,4 млрд ₽ в 2021), чистая прибыль — 12,1 млрд ₽ (6,2 млрд ₽ '
    'в 2021).'
)

OLD_LAW_STRUCT = '—'
NEW_LAW_STRUCT = (
    'По данным ЕГРЮЛ, АО «БАТ-СПб» и АО «МУМТ» перешли BFI Holding '
    '(Абу-Даби); владельцы холдинга — Фарук Енер (бывший гендиректор '
    'BAT по России, Турции, Кавказу, Центральной Азии и Белоруссии), '
    'Олег Барвин (бывший глава юридического департамента BAT), Елена '
    'Заварзина, Андрей Осаволюк и Сергей Кудинов.'
)

OLD_LAW_TERMS = '—'
NEW_LAW_TERMS = (
    'По мнению источника «Ъ» в отрасли, бывший менеджмент BAT '
    'контролирует ITMS, что может позволить BAT вернуться к владению '
    'активами при стабилизации ситуации — это предположение источника, '
    'а не подтверждённое условие сделки.'
)

NEW_SRC = [
    ['Интерфакс', 'https://www.interfax.ru/business/920832'],
    ['Интерфакс', 'https://www.interfax.ru/business/930213'],
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/6212859'],
]

BUYER_ID = 'gc551a7f5'
OLD_BUYER_IND = 'Химия и удобрения'
NEW_BUYER_IND = 'Пищепром и напитки'
OLD_BUYER_DESC = (
    'Консорциум российских инвесторов и местного менеджмента; в 2023 '
    'году получил от British American Tobacco российский и белорусский '
    'бизнес с брендами Dunhill, Kent, Vogue, Rothmans, Pall Mall, Lucky '
    'Strike.'
)
NEW_BUYER_DESC = OLD_BUYER_DESC + (
    ' После закрытия сделки активы переименованы в ITMS Group; по '
    'данным ЕГРЮЛ, конечный держатель — BFI Holding (Абу-Даби).'
)


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)
    buyer = data['companies'][BUYER_ID]

    assert deal['ind'] == OLD_IND
    assert deal['status'] == OLD_STATUS
    assert deal['sum'] == 'Не раскрыта'
    assert deal['eco']['sum'] == 'Не раскрыта'
    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['eco']['target_fin'] == OLD_ECO_TARGET_FIN
    assert deal['law']['struct'] == OLD_LAW_STRUCT
    assert deal['law']['terms'] == OLD_LAW_TERMS
    assert buyer['ind'] == OLD_BUYER_IND
    assert buyer['desc'] == OLD_BUYER_DESC

    new_src = deal['src'] + NEW_SRC

    print('=== ind: станет ===', NEW_IND)
    print('=== status: станет ===', NEW_STATUS)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== eco.target_fin: станет ===')
    print(NEW_ECO_TARGET_FIN)
    print('\n=== law.struct: станет ===')
    print(NEW_LAW_STRUCT)
    print('\n=== law.terms: станет ===')
    print(NEW_LAW_TERMS)
    print('\n=== src: добавится ===')
    for s in NEW_SRC:
        print(s)
    print('\n=== companies[gc551a7f5].ind: станет ===', NEW_BUYER_IND)
    print('=== companies[gc551a7f5].desc: станет ===')
    print(NEW_BUYER_DESC)

    if write:
        deal['ind'] = NEW_IND
        deal['status'] = NEW_STATUS
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['eco']['target_fin'] = NEW_ECO_TARGET_FIN
        deal['law']['struct'] = NEW_LAW_STRUCT
        deal['law']['terms'] = NEW_LAW_TERMS
        deal['src'] = new_src
        buyer['ind'] = NEW_BUYER_IND
        buyer['desc'] = NEW_BUYER_DESC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
