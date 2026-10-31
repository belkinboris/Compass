# -*- coding: utf-8 -*-
"""«Русал»/GIADEC (g835eac98): карточка родилась решением владельца с типом
«M&A», а источники (пресс-релиз «Русала», Reuters, ПРАЙМ, ТАСС) говорят о
создании двух совместных предприятий в Гане, а не о покупке доли. Тип
меняется на «Создание СП» (docs/card_status_dates.md «Создание СП — тип
«Создание СП»»), тема — «Создание СП», как у остальных карточек этого типа.
Через review.py тип «Создание СП» не правится (его нет в TYPE_WORDS) — тот же
путь, что у «1С»/«Райтек» (pipeline/fix_g685f1e39_jv_type_2026_10_21.py).
Участники (профили в buyer/target), проза и источники — через
accept_card.py и review.py.

Карточка лежит в очереди (static/data/pending.json); файл перечитывается
прямо перед записью. Без ключа — сухой прогон; запись — --write.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
CARD = 'g835eac98'


def patch(pending):
    card = next(c for c in pending['cards'] if c['id'] == CARD)
    assert card['type'] == 'M&A', card['type']
    assert not card.get('themes'), card.get('themes')
    assert not card.get('no_parties'), card.get('no_parties')
    card['type'] = 'Создание СП'
    card['themes'] = ['Создание СП']
    return card


def main():
    write = '--write' in sys.argv
    patch(json.load(open(PENDING, encoding='utf-8')))
    print('%s: type M&A -> Создание СП; themes = [Создание СП]' % CARD)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    pending = json.load(open(PENDING, encoding='utf-8'))   # перечитать прямо перед записью
    patch(pending)
    with open(PENDING, 'w', encoding='utf-8') as f:
        json.dump(pending, f, ensure_ascii=False, indent=1)
    print('записано')
    return 0


if __name__ == '__main__':
    sys.exit(main())
