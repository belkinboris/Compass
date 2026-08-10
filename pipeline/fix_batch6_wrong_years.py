# -*- coding: utf-8 -*-
"""Пять карточек несли `date`=«2022» (заглушка компактного импорта), хотя
единственный источник каждой сам датирован 2023 годом и описывает событие
как происходящее СЕЙЧАС («может купить», «интересуется», «выходит»,
«купил»), а не задним числом:

- g42f3065c (ГК «Рост»/тепличные комплексы): kommersant.ru/doc/5785646,
  дата в заголовке «26.01.2023, 13:51».
- gfc260e10 (Ростелеком/МегаФон): kommersant.ru/doc/5796556,
  «30.01.2023, 01:11».
- g1f43265d (ЕБРР/«Хлебпром»): kommersant.ru/doc/5772275,
  «16.01.2023, 00:36».
- gd39b4eaa (Кахидзе/«Лискимонтажконструкция»): kommersant.ru/doc/5773012,
  «17.01.2023, 00:01».
- gadd949cc (Промсвязьбанк/МИнБ): interfax.ru/business/881350,
  «10:39, 19 января 2023» — «Промсвязьбанк внес в уставной капитал 100%
  акций МИнБ... следует из данных ЕГРЮЛ», обновление «Промсвязьбанк
  завершил присоединение» — именно это событие, а не более ранние шаги
  (докапитализация 2019/2022), и датирует карточку.

- c5e3a4754 (Полюс/GV Gold, Голец Высочайший): kommersant.ru/doc/5888872,
  «23.03.2023, 01:20» (и подвал бумажного номера «№49 от 23.03.2023»).
- c220a77df (Mars/завод соусов в Луховицах): kommersant.ru/doc/5773585,
  «18.01.2023, 01:14».

Для сравнения: две другие карточки этой партии, тоже опубликованные в
конце 2022 года (g6023c156 — kommersant.ru/doc/5719027, «12.12.2022»;
g4cb8fc20 — kommersant.ru/doc/5707294, «07.12.2022»), год не меняют —
там заглушка «2022» уже совпадает с датой источника.

Седьмая карточка партии с тем же дефектом (g688aa290, Michelin/«Пауэр
Интернэшнл») исправлена отдельным скриптом
(`fix_michelin_power_international.py`) вместе со статусом и линзами.

Почему не через review.py: перенос в другой год не поддержан
`date_is_supported()` намеренно (см. прецедент
`fix_osnova_sviblovo_date.py`).

Запуск: python3 pipeline/fix_batch6_wrong_years.py
        python3 pipeline/fix_batch6_wrong_years.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

DATES = {
    'g42f3065c': '2023-01-26',
    'gfc260e10': '2023-01-30',
    'g1f43265d': '2023-01-16',
    'gd39b4eaa': '2023-01-17',
    'gadd949cc': '2023-01-19',
    'c5e3a4754': '2023-03-23',
    'c220a77df': '2023-01-18',
}


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    cards = {d['id']: d for d in data['deals']}
    todo = {}
    for cid, new in DATES.items():
        card = cards[cid]
        if card['date'] == new:
            print('УЖЕ ПРИМЕНЕНО %s' % cid)
            continue
        assert card['date'] == '2022', '%s: дата уже другая' % cid
        todo[cid] = new
        print('ПРАВИМ  %s date: «2022» -> «%s»' % (cid, new))
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
