#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Роли сделки Guess/«ГЕСС СИАЙЭС» были спутаны: покупателем стоял профиль,
который на самом деле описывает ТУ ЖЕ компанию, что и предмет сделки, а
настоящий продавец (физлицо) не был назван вовсе.

ЧТО СЛОМАНО. Карточка `g7b2a78bf` («Guess выкупил 30% долю российского
партнера Вячеслава Шикулова в местном бизнесе») хранила `buyer: g5915e68f`
(«Guess (российский бизнес)», desc: «Российское подразделение
американского бренда одежды и аксессуаров») и `target: g3b9d27f8» («ГЕСС
СИАЙЭС», desc: «Российский бизнес Guess»). Кампания самопроверки ИНН
(волна 1, 28 августа 2026) нашла, что ОБА профиля резолвятся в один и тот
же ИНН 7729482411 — потому что это буквально ОДНО И ТО ЖЕ юрлицо, названное
дважды: «Guess (российский бизнес)» и «ГЕСС СИАЙЭС» — разные названия
одной российской «дочки» Guess. Компания не может быть одновременно
покупателем и предметом собственной сделки.

ЧТО НА САМОМ ДЕЛЕ ПРОИЗОШЛО (текст самой карточки, `extra`, дословно):
«Выкуп Guess 30% доли в российском бизнесе (ГЕСС СИАЙЭС) у партнера
Вячеслава Шикулова в соответствии с пут-опционом... Опцион был исполнен
в ноябре 2022 года, разрешение OFAC получено до закрытия сделки». То есть:
  - ПРЕДМЕТ — 30% доли в ГЕСС СИАЙЭС (российское юрлицо, target остаётся
    как есть, это и так правильно);
  - ПОКУПАТЕЛЬ — сама Guess Inc. (иностранная материнская компания,
    у которой нет и не должно быть российского ИНН — она выкупает долю
    СВОЕЙ ЖЕ российской «дочки» у миноритария);
  - ПРОДАВЕЦ — Вячеслав Шикулов, физлицо (российский партнёр, держатель
    пут-опциона 2015 года) — этого поля не было вовсе.

ПОЧЕМУ buyer_name, А НЕ ПРОФИЛЬ. У Guess Inc. нет юрлица в РФ — текстом,
тем же способом, что уже применяется к иностранным покупателям без
профиля (`buyer_name`, CLAUDE.md: «две формы записи... вторая для
инвестиционных раундов, где профилей у фондов почти нет» — тот же приём
годится для любого иностранного покупателя без ИНН). Продавец (Шикулов,
физлицо) в поле `seller` уже был назван верно — правки не требует, только
роль покупателя.

Профиль `g5915e68f» удаляется — он использовался РОВНО в этой одной роли
этой одной сделки (проверено) и не пережил бы более раннюю правку
(«одинокий company_id, оставшийся без единой роли, — не профиль, а
мусор»); переименовывать его незачем — правильное название («Guess Inc.»)
не company_id, а текст.

Запуск:
    python3 pipeline/fix_guess_gess_ciayes_roles.py            # сухой прогон
    python3 pipeline/fix_guess_gess_ciayes_roles.py --write    # записать
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'
DEAL_ID = 'g7b2a78bf'
WRONG_BUYER = 'g5915e68f'
WRONG_BUYER_NAME = 'Guess (российский бизнес)'
NEW_BUYER_NAME = 'Guess Inc.'
EXPECTED_SELLER = 'Вячеслав Шикулов'
REFS = ('buyer', 'seller_id', 'target', 'asset_id')


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    companies = data['companies']
    match_keys = data['match_keys']

    deal = by_id.get(DEAL_ID)
    assert deal is not None, 'нет сделки %s' % DEAL_ID
    assert deal.get('buyer') == WRONG_BUYER, \
        '%s: buyer уже не %s (сейчас %r)' % (DEAL_ID, WRONG_BUYER, deal.get('buyer'))
    assert not deal.get('buyer_name'), 'buyer_name уже заполнен: %r' % deal.get('buyer_name')
    assert deal.get('seller') == EXPECTED_SELLER and not deal.get('seller_id'), \
        'продавец уже не тот: seller=%r seller_id=%r' % (deal.get('seller'), deal.get('seller_id'))

    wrong = companies.get(WRONG_BUYER)
    assert wrong is not None and wrong.get('name') == WRONG_BUYER_NAME, \
        '%s: имя профиля не совпадает: %r' % (WRONG_BUYER, wrong.get('name') if wrong else None)

    refs = [d['id'] for d in data['deals']
            if WRONG_BUYER in (d.get(f) for f in REFS)]
    assert refs == [DEAL_ID], 'профиль %s используется не только в %s: %r' % (WRONG_BUYER, DEAL_ID, refs)

    print('Сделка: %s | %s' % (DEAL_ID, deal.get('title')))
    print('Было buyer=%s (%r)' % (WRONG_BUYER, WRONG_BUYER_NAME))
    print('Станет buyer_name=%r (seller=%r уже был верен)' % (NEW_BUYER_NAME, EXPECTED_SELLER))
    print('Удаляется профиль-дубль %s (%r) — та же компания, что и target (ГЕСС СИАЙЭС)' % (
        WRONG_BUYER, WRONG_BUYER_NAME))

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return

    deal['buyer'] = None
    deal['buyer_name'] = NEW_BUYER_NAME
    companies.pop(WRONG_BUYER)
    match_keys.pop(WRONG_BUYER, None)

    assert by_id[DEAL_ID]['buyer'] is None
    assert by_id[DEAL_ID]['buyer_name'] == NEW_BUYER_NAME
    assert WRONG_BUYER not in companies

    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('\nЗаписано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
