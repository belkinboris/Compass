# -*- coding: utf-8 -*-
"""Карточка `g39fc7468` («Липецкое мясо» / «Телтекс Системс»), очередь
`pending.json` — `law.struct` по данным ЕГРЮЛ (история участников,
datanewton, см. `pipeline/fix_lipetskoe_myaso_seller_status_2026_10_31.py`),
а не по статье: `review.py`/`write_card.py` сверяют цитату прозы с текстами
на диске (`data/inbox/raw/*-articles.jsonl`), и запись реестра там не
лежит — поэтому прямым скриптом, как и продавец/статус той же карточки.

Запуск: python3 pipeline/fix_lipetskoe_myaso_law_struct_2026_10_31.py
        python3 pipeline/fix_lipetskoe_myaso_law_struct_2026_10_31.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')

DEAL_ID = 'g39fc7468'
OLD_STRUCT = '—'
NEW_STRUCT = ('По данным ЕГРЮЛ, «Телтекс Системс» вошла в капитал «Липецкого мяса» ещё '
              'в июле 2026 года, получив 20% — тогда свои доли уменьшили Сергей Медведев '
              '(с 65% до 50%) и Сергей Оганов (с 32,5% до 27,5%). 27 октября 2026 года '
              'Медведев вышел из состава участников, и его 50% перешли «Телтекс Системс», '
              'доведя ее пакет до 70%; доля Оганова не менялась.')
REGISTRY_URL = ('https://datanewton.ru/api/v2/history?ogrn=1214800015022'
                 '&startDate=2000-01-01&attributes=OWNERS')


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    card = next(c for c in data['cards'] if c['id'] == DEAL_ID)

    assert card['law']['struct'] == OLD_STRUCT, card['law']['struct']

    print('=== law.struct: станет ===')
    print(NEW_STRUCT)

    if write:
        card['law']['struct'] = NEW_STRUCT
        if REGISTRY_URL not in {s[1] for s in card.get('src') or [] if len(s) > 1}:
            card.setdefault('src', []).append(
                ['ЕГРЮЛ — история участников «Липецкого мяса» (datanewton)', REGISTRY_URL])
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
