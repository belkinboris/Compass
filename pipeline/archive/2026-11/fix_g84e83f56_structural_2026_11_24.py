# -*- coding: utf-8 -*-
"""Карточка g84e83f56 (24 ноября 2026, приемка): «Белгородская область
продала 9% ППК «Черноземье» за 450 тыс. рублей» — структурные поля, которые
`review.py` не берет напрямую (покупатель-физлицо, сумма в тысячах рублей —
`sum_is_supported` понимает только млн/млрд, см. docs/card_editing.md).

Источник (Абирег, полный текст забран `fetch_article_texts.py g84e83f56
--write`, data/inbox/raw/2026-11-24-articles.jsonl): Евгений Галкин выиграл
аукцион по продаже 9% акций АО «ППК «Черноземье»», предложив около
450,1 тыс. рублей при начальной цене пакета 1 рубль.

Карточка живет только в pending.json (`accept_card.find_card` смотрит и
туда, и в deals_promoted.json) — правим файл очереди.

Запуск: python3 pipeline/archive/2026-11/fix_g84e83f56_structural_2026_11_24.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402

PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
DEAL_ID = 'g84e83f56'
BY = 'приемка, 24 ноября 2026'
URL = ('https://abireg.ru/newsitem/119505-belgorodskaya-oblast-prodala-9-'
       'ppk-chernozeme-za-450-tys-rubley/')

BUYER_QUOTE = 'Евгений Галкин выиграл аукцион по продаже принадлежащих Белгородской области 9% акций'
SUM_QUOTE = 'он предложил около 450,1 тыс. рублей'


def main(write=False):
    data = json.load(open(PENDING, encoding='utf-8'))
    card = next(c for c in data['cards'] if c['id'] == DEAL_ID)

    assert card.get('buyer_name') is None, 'buyer_name уже стоит — правку надо пересмотреть'
    assert card.get('sum') is None, 'sum уже стоит — правку надо пересмотреть'
    assert card['eco']['sum'] == '—', 'eco.sum уже стоит — правку надо пересмотреть'

    card['buyer_name'] = 'Евгений Галкин'
    card['sum'] = '450,1 тыс. рублей'
    card['eco']['sum'] = '450,1 тыс. рублей'

    fact_edit_guard.log(card, 'buyer_name', 'Евгений Галкин', BUYER_QUOTE, URL, BY)
    fact_edit_guard.log(card, 'sum', '450,1 тыс. рублей', SUM_QUOTE, URL, BY)
    fact_edit_guard.log(card, 'eco.sum', '450,1 тыс. рублей', SUM_QUOTE, URL, BY)

    print('buyer_name -> %r' % card['buyer_name'])
    print('sum -> %r' % card['sum'])
    print('eco.sum -> %r' % card['eco']['sum'])

    if write:
        data = json.load(open(PENDING, encoding='utf-8'))  # перечитать прямо перед записью
        card = next(c for c in data['cards'] if c['id'] == DEAL_ID)
        card['buyer_name'] = 'Евгений Галкин'
        card['sum'] = '450,1 тыс. рублей'
        card['eco']['sum'] = '450,1 тыс. рублей'
        fact_edit_guard.log(card, 'buyer_name', 'Евгений Галкин', BUYER_QUOTE, URL, BY)
        fact_edit_guard.log(card, 'sum', '450,1 тыс. рублей', SUM_QUOTE, URL, BY)
        fact_edit_guard.log(card, 'eco.sum', '450,1 тыс. рублей', SUM_QUOTE, URL, BY)
        with open(PENDING, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('записано')
    else:
        print('сухой прогон — запись с --write')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
