# -*- coding: utf-8 -*-
"""Карточка `g5da91c40` (ЕМС/«Семейный доктор»): ревизия (batch_a_rev04,
коммит ce3a7b6) заменила `sum`/`eco.sum` с оценочного диапазона
«13–20 млрд ₽ (по оценке)» на официальную сумму «17,6 млрд ₽» — Интерфакс
01.11.2025 со ссылкой на саму EMC. Но `eco.rationale` и `extra` (тот же
текст в обоих полях) остались нетронуты и прямо противоречат уже
исправленным полям: «Официальная сумма не разглашается... 13-20 млрд руб.
(оценка экспертов, официальная сумма не разглашается)» — рядом с суммой
«17,6 млрд ₽» на тех же вкладках карточки. Факт не новый и не требует
повторной проверки цитатой: он уже подтверждён источником, добавленным
той же ревизией (Интерфакс, https://www.interfax.ru/business/1055991) —
здесь только перенос уже установленного факта во второе поле, где он
раньше не был обновлён (тот же класс урока, что «Сумма на «Обзоре» и
сумма в «Экономисте» — два разных поля»).

Запуск: python3 pipeline/fix_ems_semeyny_doktor_rationale.py
        python3 pipeline/fix_ems_semeyny_doktor_rationale.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g5da91c40'
OLD_TEXT = ('Закрытая сделка M&A между Европейским медицинским центром '
            '(покупатель) и Владиславом Тимохиным (продавец 75% акций). '
            'Официальная сумма не разглашается; эксперты оценивают '
            'стоимость бизнеса (EV) в диапазоне 13-20 млрд руб. Сумма: '
            '13-20 млрд руб. (оценка экспертов, официальная сумма не '
            'разглашается).')
NEW_TEXT = ('Закрытая сделка M&A между Европейским медицинским центром '
            '(покупатель) и Владиславом Тимохиным (продавец 75% акций). '
            'Официальная сумма сделки — 17,6 млрд руб. (раскрыта EMC, по '
            'данным Интерфакса); ранее эксперты оценивали стоимость '
            'бизнеса (EV) в 13–20 млрд руб.')


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == CARD_ID)
    assert card['sum'] == '17,6 млрд ₽', 'sum уже другой — проверь карточку заново'
    assert card['eco']['sum'] == '17,6 млрд ₽', 'eco.sum уже другой'
    if card['eco']['rationale'] == NEW_TEXT and card['extra'] == NEW_TEXT:
        print('УЖЕ ПРИМЕНЕНО %s' % CARD_ID)
        return
    assert card['eco']['rationale'] == OLD_TEXT, 'eco.rationale уже другой'
    assert card['extra'] == OLD_TEXT, 'extra уже другой'
    print('ПРАВИМ %s: eco.rationale и extra — убираем противоречие с '
          'уже исправленной суммой' % CARD_ID)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    card['eco']['rationale'] = NEW_TEXT
    card['extra'] = NEW_TEXT
    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
