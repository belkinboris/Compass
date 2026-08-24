# -*- coding: utf-8 -*-
"""Месячная очередь, карточка gf985bad7 (спиртзавод №14): дельта-поиск
вскрыл, что `buyer` этой карточки — 'rencap' ('Ренессанс Капитал',
инвестбанк, ключевое лицо Максим Орловский) — профиль СОВСЕМ ДРУГОЙ
компании. Сделка — про ООО «Ренессанс», второго по объёму производителя
спирта в России (создан в 2018 году Александром Русаковым, сейчас 51%
через ООО «Оникс» контролирует ЗПИФ «Центр проф», 49% — у Алины
Чочаевой, гендиректор — Максим Текутьев), не имеющего никакого
отношения к инвестбанку. Тот же ошибочный buyer стоит и у карточки
ge2e2c71c («Ренессанс» выкупил 25% «Евразийской алкогольной группы») —
тот же спиртовой «Ренессанс», не банк. Профиль 'rencap' используется
верно в двух других карточках (citibank, g995f83cf) — его не трогаем,
только отвязываем от него две алкогольные сделки.

Родня уже записанного класса «Стороной сделки может быть записан
профиль совсем другой сущности» (ЛСР/Domina Пулково) — здесь профиль
не испорчен по имени, а совпадение слова «Ренессанс» в разных отраслях
привело к тому, что при разборе притока сторона получила ссылку на
уже существующий, но НЕВЕРНЫЙ профиль.

Заводим новый профиль спиртового «Ренессанса» (имя с уточнением в
скобках — чтобы не совпасть по транслитерационному ключу с «Ренессанс
Капитал» и с СК «Ренессанс Жизнь», тот же приём, что и «Кама» (Атом))
и перевязываем buyer обеих карточек на него.

Источник — читал напрямую (fetch_article_texts.py, закэширован):
https://www.kommersant.ru/doc/7870281

Запуск: python3 pipeline/fix_renessans_alcohol_buyer_profile.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

NEW_ID = 'g_renessans_spirt'
NEW_COMPANY = {
    'name': '«Ренессанс» (спиртовая группа)',
    'ind': 'Пищепром и напитки',
    'desc': (
        'Второй по объёму производитель спирта в России, основное '
        'производство — в Кабардино-Балкарии. Компанию создал в 2018 '
        'году Александр Русаков (бывший владелец ООО «Торговый дом '
        '«Русалко»»); сейчас 51% через ООО «Оникс» контролирует ЗПИФ '
        '«Центр проф», 49% — у Алины Чочаевой. Гендиректор — Максим '
        'Текутьев.'
    ),
}

DEAL_IDS = ('gf985bad7', 'ge2e2c71c')


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    companies = data['companies']

    assert NEW_ID not in companies, f'{NEW_ID} уже существует'

    for did in DEAL_IDS:
        deal = next(d for d in data['deals'] if d['id'] == did)
        assert deal['buyer'] == 'rencap', (
            f'{did}: buyer уже не rencap ({deal["buyer"]!r})'
        )

    print('Новый профиль:', NEW_ID, '=', NEW_COMPANY['name'])
    for did in DEAL_IDS:
        print(f'{did}: buyer rencap -> {NEW_ID}')

    if write:
        companies[NEW_ID] = NEW_COMPANY
        for did in DEAL_IDS:
            deal = next(d for d in data['deals'] if d['id'] == did)
            deal['buyer'] = NEW_ID
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('ЗАПИСАНО')
    else:
        print('Сухой прогон. Запись — с --write.')


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
