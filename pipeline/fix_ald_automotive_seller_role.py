#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Продавец сделки АЛД Автомотив/Игорь Ким ссылался на профиль, который на
самом деле описывает ТОТ ЖЕ российский актив, что и предмет сделки, —
тот же класс, что уже исправлен для Guess/«ГЕСС СИАЙЭС»
(pipeline/fix_guess_gess_ciayes_roles.py).

ЧТО СЛОМАНО. Карточка `g2d653619` («ALD Automotive продала лизинговую
компанию в России структурам Игоря Кима») хранила `seller_id: gb0cdbc40`
(«ALD Automotive Russia», desc: «Российская лизинговая компания ALD
Automotive»). Кампания самопроверки ИНН (волна 2, 28 августа 2026) нашла,
что этот профиль резолвится в ТОТ ЖЕ ИНН 7725514969, что и `target`
карточки — `g95fe3191` («ООО «АЛД Автомотив»», desc: «...последний актив
Société Générale в стране; в 2023 году продана структурам Игоря Кима»).
Профиль-«продавец» и профиль-«предмет» оказались одной и той же реальной
российской компанией — компания не может продавать сама себя.

ЧТО НА САМОМ ДЕЛЕ ПРОИЗОШЛО. Текстовое поле `seller` уже называло
настоящего продавца верно: «ALD Automotive» (французская компания,
дочерняя структура Société Générale — `extra` дословно: «ALD Automotive
(французская компания, дочерняя компания Société Générale) продала
российскую лизинговую компанию ООО «АЛД Автомотив»...»). У французской
ALD Automotive нет и не должно быть российского ИНН — она иностранный
продавец, лизинговую «дочку» в РФ (ООО «АЛД Автомотив») продающий, а не
сама эта «дочка». Ссылка `seller_id` на `gb0cdbc40` была лишней и
ошибочной: `seller` текстом уже нёс верное имя, `seller_id` дублировал
`target`.

Профиль `gb0cdbc40` удаляется — использовался РОВНО в этой одной роли
этой одной сделки (проверено), переименовывать незачем: он не несёт
отдельного значения, текст `seller` уже полон.

Запуск:
    python3 pipeline/fix_ald_automotive_seller_role.py            # сухой прогон
    python3 pipeline/fix_ald_automotive_seller_role.py --write    # записать
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'
DEAL_ID = 'g2d653619'
WRONG_SELLER_ID = 'gb0cdbc40'
WRONG_SELLER_NAME = 'ALD Automotive Russia'
EXPECTED_SELLER_TEXT = 'ALD Automotive'
EXPECTED_TARGET = 'g95fe3191'
REFS = ('buyer', 'seller_id', 'target', 'asset_id')


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    companies = data['companies']
    match_keys = data['match_keys']

    deal = by_id.get(DEAL_ID)
    assert deal is not None, 'нет сделки %s' % DEAL_ID
    assert deal.get('seller_id') == WRONG_SELLER_ID, \
        '%s: seller_id уже не %s (сейчас %r)' % (DEAL_ID, WRONG_SELLER_ID, deal.get('seller_id'))
    assert deal.get('seller') == EXPECTED_SELLER_TEXT, \
        'seller уже не тот: %r' % deal.get('seller')
    assert deal.get('target') == EXPECTED_TARGET, \
        'target уже не тот: %r' % deal.get('target')

    wrong = companies.get(WRONG_SELLER_ID)
    assert wrong is not None and wrong.get('name') == WRONG_SELLER_NAME, \
        '%s: имя профиля не совпадает: %r' % (WRONG_SELLER_ID, wrong.get('name') if wrong else None)

    refs = [d['id'] for d in data['deals']
            if WRONG_SELLER_ID in (d.get(f) for f in REFS)]
    assert refs == [DEAL_ID], 'профиль %s используется не только в %s: %r' % (WRONG_SELLER_ID, DEAL_ID, refs)

    print('Сделка: %s | %s' % (DEAL_ID, deal.get('title')))
    print('Было seller_id=%s (%r), seller=%r' % (WRONG_SELLER_ID, WRONG_SELLER_NAME, EXPECTED_SELLER_TEXT))
    print('Станет seller_id=None, seller=%r (без изменений)' % EXPECTED_SELLER_TEXT)
    print('Удаляется профиль-дубль %s (%r) — та же компания, что и target (ООО «АЛД Автомотив»)' % (
        WRONG_SELLER_ID, WRONG_SELLER_NAME))

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return

    deal['seller_id'] = None
    companies.pop(WRONG_SELLER_ID)
    match_keys.pop(WRONG_SELLER_ID, None)

    assert by_id[DEAL_ID]['seller_id'] is None
    assert by_id[DEAL_ID]['seller'] == EXPECTED_SELLER_TEXT
    assert WRONG_SELLER_ID not in companies

    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('\nЗаписано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
