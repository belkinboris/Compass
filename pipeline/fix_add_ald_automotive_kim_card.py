# -*- coding: utf-8 -*-
"""Заметка 496 (консоль, 4 сентября 2026): «Отдельная карточка», отвечая
на карточку `gc1a34417» («Менеджмент и финансовый инвестор приобрели
Deutsche Leasing Восток и АЛД Автомотив у Deutsche Leasing AG»).

Известная проблема (CLAUDE.md): заголовок и профиль `gcd03a064» сводили
ДВЕ РАЗНЫЕ сделки с ДВУМЯ РАЗНЫМИ продавцами в одну карточку — источник
(Коммерсантъ) описывает и продажу «Дойче Лизинг Восток» (Deutsche
Leasing AG → менеджмент/инвестор), и ОТДЕЛЬНУЮ продажу «АЛД Автомотив»
(Societe Generale → АО «ЦК», структуры Игоря Кима). Обе стороны второй
сделки УЖЕ верно описаны в профилях компаний (`g95fe3191» «ООО «АЛД
Автомотив»» и `ge370cfae» «Структуры Игоря Кима»), просто отдельной
карточки для неё не было. Профиль `gcd03a064» переименован — убрано
упоминание «АЛД Автомотив», которого эта сделка не касалась.

Запуск: python3 pipeline/fix_add_ald_automotive_kim_card.py [--write]
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ingest'))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

NEW_ID = 'g7a36bc0c'
OLD_TARGET_NAME = 'Deutsche Leasing Восток и АЛД Автомотив'
NEW_TARGET_NAME = 'Deutsche Leasing Восток'
OLD_TARGET_DESC = (
    'Лизинговый и факторинговый бизнес немецкой Deutsche Leasing AG в '
    'России (сумма сделки оценивается в ~7 млрд ₽); в 2023 году их '
    'купили менеджмент российских компаний и неназванный финансовый '
    'инвестор.'
)
NEW_TARGET_DESC = (
    'Лизинговый и факторинговый бизнес немецкой Deutsche Leasing AG в '
    'России (сумма сделки оценивается в ~7 млрд ₽); в 2023 году его '
    'купили менеджмент российских компаний и неназванный финансовый '
    'инвестор. 23 мая 2023 года переименована в АО «Дойче Финанс '
    'Восток».'
)


def main(write=False):
    import promote

    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    ids = {c['id'] for c in data['deals']}
    assert NEW_ID not in ids
    assert data['companies']['gcd03a064']['name'] == OLD_TARGET_NAME
    assert data['companies']['gcd03a064']['desc'] == OLD_TARGET_DESC
    assert data['companies'].get('g95fe3191', {}).get('name') == 'ООО «АЛД Автомотив»'
    assert data['companies'].get('ge370cfae', {}).get('name') == 'Структуры Игоря Кима'

    data['companies']['gcd03a064']['name'] = NEW_TARGET_NAME
    data['companies']['gcd03a064']['desc'] = NEW_TARGET_DESC

    draft = {
        'date': '2023',
        'title': 'Структуры Игоря Кима купили «АЛД Автомотив» у Societe Generale',
        'ind': 'Транспорт и логистика',
        'type': 'M&A',
        'status': 'Закрыта',
        'seller': 'Societe Generale',
        'src': [['Коммерсантъ', 'https://www.kommersant.ru/doc/5979256'],
                ['Интерфакс', 'https://www.interfax.ru/business/901557']],
    }
    card = promote.to_card(draft, NEW_ID)
    card['buyer'] = 'ge370cfae'
    card['target'] = 'g95fe3191'
    card['eco']['context'] = (
        '«АЛД Автомотив» — последний актив Societe Generale в России. '
        'Связь покупателя со структурами Альфа-Банка (упомянутая в '
        'исходной статье применительно к сделке с Deutsche Leasing '
        'Восток) к этой сделке не относится — здесь конечный покупатель '
        '— структуры банкира Игоря Кима, владельца Экспобанка, уже '
        'купившие к тому времени российские лизинговые «дочки» '
        'Volkswagen, Volvo и CNH Industrial.'
    )

    data['deals'].append(card)
    print(f'Добавлена карточка {NEW_ID}: {card["title"]}')
    print('Профиль gcd03a064 переименован (снято «АЛД Автомотив»)')

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Записано.')
    else:
        print('(сухой прогон, для записи — --write)')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
