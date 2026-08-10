# -*- coding: utf-8 -*-
"""Ревизия 2024 (batch_d_rev06) нашла ещё одну протёкшую служебную пометку
роли — тот же класс, что уже чинили `fix_batch_d_n06_wrong_years_and_tags.py`
(g5792754e, geb946158, g4577126f, cef2d9366, g2d075f03) и rev03 (gb6a90572):
`eco.rationale`/`extra` синтезированы компактным импортом и несут на конце
служебную пометку роли покупателя/продавца, не являющуюся дословной цитатой
источника, поэтому снятие не проходит через `review.py` (там нет цитаты для
сверки), но само снятие — не перенос факта, а вычищение уже присутствующего
в базе текста:

- g5b4a3bf8 (ГК «Таврос»/United buns): «(Структуры ГК «Таврос»
  (покупатель))» — тег стоит в поле `extra` (не в `eco.rationale`, который
  у этой карточки уже содержит другой, чистый текст).

Запуск: python3 pipeline/fix_batch_d_rev06_leaked_tag.py
        python3 pipeline/fix_batch_d_rev06_leaked_tag.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g5b4a3bf8'
FIELD = 'extra'
OLD_FULL = (
    'Сделка по приобретению подмосковного производителя мучных изделий ООО '
    '«Гипфель» (United buns). Агрохолдинг «Таврос» расширяет присутствие в '
    'сегменте производства булочек для фастфуда, дополняя собственное '
    'производство «Багерстат Рус». Сумма: 2,5 млрд рублей (оценка '
    'экспертами с учетом долга). (Структуры ГК «Таврос» (покупатель))'
)
TAG = ' (Структуры ГК «Таврос» (покупатель))'


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == CARD_ID)
    new_full = OLD_FULL[:-len(TAG)]

    if card[FIELD] == new_full:
        print('УЖЕ ПРИМЕНЕНО')
        return

    assert card[FIELD] == OLD_FULL, '%s: значение уже другое' % FIELD
    print('ПРАВИМ  %s %s: снята протёкшая пометка роли' % (CARD_ID, FIELD))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    card[FIELD] = new_full
    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
