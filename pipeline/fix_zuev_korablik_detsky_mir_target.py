#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Предмет сделки перепутан со скобочным пояснением о покупателе.

ЧТО СЛОМАНО. Карточка `g22000f22` («Приобретение консорциумом Алексея Зуева
(«Кораблик») 29,9% акций «Детского мира» у бывших топ-менеджеров «Полюса»»)
хранит `target: "gd2431ed3"` — профиль «Кораблик» (сеть детских товаров).
Но «Кораблик» в заголовке — это ПОЯСНЕНИЕ, кто такой Зуев (её основатель),
а не предмет сделки: сама сделка — покупка 29,9% акций ПАО «Детский мир»
(`extra` дословно: «Итоговый пакет Зуева с партнёрами составил 29,9%
уставного капитала «Детского мира»»). Классический случай «предмет,
вырезанный из заголовка не тем куском» — родня уже описанных в CLAUDE.md
(«Стороной сделки может быть записан профиль совсем другой сущности»,
«Название в кавычках — часто не предмет сделки, а продавец»), только здесь
перепутан не продавец, а сам предмет со скобочным эпитетом покупателя.

Профиль «ПАО «Детский мир»» (`g47bca1da`) уже существует в базе — им же
верно помечены соседние карточки той же истории (`g76159e00` «Дмитрий
Кленов продал 10% акций «Детского мира»», `g50c555a0` «Детский мир завершил
трансформацию…»).

Запуск:
    python3 pipeline/fix_zuev_korablik_detsky_mir_target.py            # сухой прогон
    python3 pipeline/fix_zuev_korablik_detsky_mir_target.py --write    # записать
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'
DEAL_ID = 'g22000f22'
WRONG_TARGET = 'gd2431ed3'
WRONG_TARGET_NAME = 'Кораблик'
RIGHT_TARGET = 'g47bca1da'
RIGHT_TARGET_NAME = 'ПАО «Детский мир»'


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    companies = data['companies']

    deal = by_id.get(DEAL_ID)
    assert deal is not None, 'нет сделки %s' % DEAL_ID
    assert deal.get('target') == WRONG_TARGET, \
        '%s: target уже не %s (сейчас %r) — правка уже применена или сделка изменилась' % (
            DEAL_ID, WRONG_TARGET, deal.get('target'))
    assert 'Детского мира' in (deal.get('title') or ''), \
        '%s: заголовок больше не называет «Детский мир» — проверить вручную' % DEAL_ID

    wrong = companies.get(WRONG_TARGET)
    assert wrong is not None and wrong.get('name') == WRONG_TARGET_NAME, \
        '%s: имя профиля не совпадает: %r' % (WRONG_TARGET, wrong.get('name') if wrong else None)
    right = companies.get(RIGHT_TARGET)
    assert right is not None and right.get('name') == RIGHT_TARGET_NAME, \
        '%s: имя профиля не совпадает: %r' % (RIGHT_TARGET, right.get('name') if right else None)

    print('Сделка: %s | %s' % (DEAL_ID, deal.get('title')))
    print('Было target=%s (%r)' % (WRONG_TARGET, WRONG_TARGET_NAME))
    print('Станет target=%s (%r)' % (RIGHT_TARGET, RIGHT_TARGET_NAME))
    print('Профиль %s (%r) остаётся в базе — после правки без этой сделки.' % (WRONG_TARGET, WRONG_TARGET_NAME))

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return

    deal['target'] = RIGHT_TARGET
    assert by_id[DEAL_ID]['target'] == RIGHT_TARGET

    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('\nЗаписано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
