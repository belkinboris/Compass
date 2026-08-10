# -*- coding: utf-8 -*-
"""Ревизия 2024 (batch_d_rev04) вскрыла два случая смещения года почти на
целый год (декабрь 2024 → 2025):

- gcdf7065a (Владислав Бакальчук/Wildberries): собственные поля карточки
  (law.struct) уже упоминали «в апреле сообщалось» и «в ноябре
  сообщалось» — хронология, укладывающаяся только в 2025 год. Обязательный
  поиск подтвердил: сделка (переход 1% Ким по решению суда) произошла
  10 декабря 2025 года (moskvichmag.ru, ura.news, РБК — все три источника
  датированы 10.12.2025), а не 2024-го. Дата: «2024-12-10» -> «2025-12-10».
- c6fd3a848 (передача «Волга-Днепр» государству): единственный источник
  карточки (kommersant.ru/doc/7988696) сам датирован 24.08.2025, 21:09 —
  заявление Алексея Исайкина на праздновании 35-летия компании, а не
  декабрь 2024 года. Дата: «2024-12-04» -> «2025-08-24».

Перенос в другой год `date_is_supported()` не поддерживает намеренно (см.
прецедент `fix_osnova_sviblovo_date.py`).

Запуск: python3 pipeline/fix_batch_d_rev04_wrong_years.py
        python3 pipeline/fix_batch_d_rev04_wrong_years.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

DATES = {
    'gcdf7065a': ('2024-12-10', '2025-12-10'),
    'c6fd3a848': ('2024-12-04', '2025-08-24'),
}


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    cards = {d['id']: d for d in data['deals']}
    todo = {}
    for cid, (old, new) in DATES.items():
        card = cards[cid]
        if card['date'] == new:
            print('УЖЕ ПРИМЕНЕНО %s' % cid)
            continue
        assert card['date'] == old, '%s: дата уже другая (%r)' % (cid, card['date'])
        todo[cid] = new
        print('ПРАВИМ  %s date: «%s» -> «%s»' % (cid, old, new))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    for cid, new in todo.items():
        cards[cid]['date'] = new
    if todo:
        json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
