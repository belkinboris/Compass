# -*- coding: utf-8 -*-
"""Убрать карточку g784c5e92 (Сбербанк продаёт права требования к
застройщику ЖК «Новый город» в Выборге) — заметка владельца в консоли
23 сентября 2026, 14:23 МСК (id решения 750): «не на ту кнопку нажал,
продажа прав требования это не сделка не делай карточку».

ЗАЧЕМ УДАЛЕНИЕ, А НЕ ПРАВКА. Владелец отклоняет не поле карточки, а САМ
КЛАСС: продажа/уступка прав требования по кредиту (цессия долга) — не
сделка M&A в его понимании продукта, а не «неточно описанная сделка».
Правкой полей это не лечится.

ГРАНИЦА. Удаляется ТОЛЬКО эта карточка, только если пост в канал НЕ
уходил (`telegram_posts['g784c5e92']` — None, `no_post: True` уже стоит
в карточке) и заголовок совпадает — та же защита, что в
`remove_out_of_scope_deals.py`. Профиль застройщика-должника
(`g7c41b555`, ИНН 4704075867) и запись в `fns_registry.py` НЕ трогаются:
это настоящее, проверенное по ЕГРЮЛ юрлицо, орфанный профиль без сделки
не вредит и может пригодиться, если компания попадёт в другую историю.

Правило на будущее (не код, для памяти рутины): продажа/уступка прав
требования по кредиту застройщика — не сделка для этой базы, к
триаж-фильтру `promote.py` не относится (это решение о СМЫСЛЕ, не о
форме черновика), запись — в KNOWN_ISSUES.md.

Запуск:
    python3 pipeline/remove_not_a_deal_2026_09_23.py            # сухой прогон
    python3 pipeline/remove_not_a_deal_2026_09_23.py --write    # удалить
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g784c5e92'
TITLE_PART = 'Сбербанк продаёт права требования'


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((d for d in data['deals'] if d['id'] == DEAL_ID), None)
    if not card:
        print('НЕ ТРОГАЕМ %s — карточки уже нет в базе' % DEAL_ID)
        return 0
    if TITLE_PART.lower() not in str(card.get('title') or '').lower():
        print('НЕ ТРОГАЕМ %s — заголовок не совпадает: %r' % (DEAL_ID, card.get('title')))
        return 1
    posted = data.get('telegram_posts', {}).get(DEAL_ID)
    if posted:
        print('НЕ ТРОГАЕМ %s — пост в канал уже уходил, удалять карточку с опубликованным постом нельзя' % DEAL_ID)
        return 1
    print('УДАЛЯЕМ %s %s' % (DEAL_ID, card['title']))
    print('         пост в канал не уходил (no_post=%r), причина — заметка владельца в консоли' % card.get('no_post'))
    if not write:
        print('\nСухой прогон. Удаление — с ключом --write.')
        return 0
    before = len(data['deals'])
    data['deals'] = [d for d in data['deals'] if d['id'] != DEAL_ID]
    assert len(data['deals']) == before - 1, 'удалилось не то количество'
    data.get('telegram_posts', {}).pop(DEAL_ID, None)
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nУДАЛЕНО: 1 (в базе было %d, стало %d)' % (before, len(data['deals'])))
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
