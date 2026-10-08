# -*- coding: utf-8 -*-
"""Карточка `gd8faa2c4` (Инфамед/«Мирамистин») — новый этап: Верховный суд
отказал Ирине Хугаевой в пересмотре дела о законности продажи 50% доли
Оксане Хейфиц (кассационная жалоба по отдельной жалобе экс-гендиректора
Николаева о 99,9% пока не рассмотрена).

Источник: https://ria.ru/20261008/sud-2123106759.html

    python3 pipeline/fix_gd8faa2c4_vs_cassation.py           # показать
    python3 pipeline/fix_gd8faa2c4_vs_cassation.py --write   # записать
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__)).rsplit(os.sep, 1)[0]
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
DEAL = 'gd8faa2c4'

NOTE = (
    'Верховный суд России отказал бывшей единоличной собственнице ООО '
    '"Инфамед" Ирине Хугаевой, просившей пересмотреть выводы нижестоящих '
    'инстанций о законности договора, по которому она продала долю в 50% '
    'в компании Оксане Хейфиц. Поданная в высшую судебную инстанцию позже '
    'аналогичная жалоба бывшего гендиректора "Инфамеда" Виталия Николаева '
    'пока не рассмотрена.'
)

NEW_EVENT = {
    'kind': 'court',
    'date': '2026-10-08',
    'title': 'ВС отказал в пересмотре дела о продаже 50% доли',
    'note': NOTE,
    'source': ['РИА Новости', 'https://ria.ru/20261008/sud-2123106759.html'],
}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))   # перечитано прямо перед записью
    deal = next(d for d in data['deals'] if d['id'] == DEAL)
    existing = [(e.get('kind'), e.get('date')) for e in deal.get('events') or []]
    assert (NEW_EVENT['kind'], NEW_EVENT['date']) not in existing, 'такой этап уже есть'
    deal.setdefault('events', []).append(NEW_EVENT)
    deal['events'].sort(key=lambda e: (str(e.get('date') or ''), str(e.get('kind') or '')))
    print('Этап добавлен: %s (%s)' % (NEW_EVENT['title'], NEW_EVENT['date']))
    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('записано')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
