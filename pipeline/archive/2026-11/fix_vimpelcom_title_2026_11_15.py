# -*- coding: utf-8 -*-
"""Карточка g64a94e27: в заголовке покупателем названа компания, а не «топ-менеджеры».

Партнер, 15 ноября 2026: «это не топ-менеджеры, а просто структура, в которой номинально сели
менеджеры»; оплата прошла еврооблигациями VEON, которые выкупил сам «ВымпелКом» (это уже есть в
поле eco.fin карточки). Покупатель по карточке — «Коперник-Инвест 3» (профиль buyer), поэтому
заголовок называет его, а кто владеет покупателем, остается в тексте карточки.

    python3 pipeline/archive/2026-11/fix_vimpelcom_title_2026_11_15.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import review  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
CID = 'g64a94e27'
OLD = 'Топ-менеджеры «ВымпелКома» купили компанию у VEON за 130 млрд ₽'
NEW = '«Коперник-Инвест 3» купил «ВымпелКом» у VEON за 130 млрд ₽'


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))      # читается прямо перед записью
    c = next(d for d in data['deals'] if d['id'] == CID)
    fp = review.fix_fingerprint(OLD)      # запись таблицы FIXES ставила прежний заголовок (docs/card_editing.md)
    marks = c.setdefault('proofread_absorbed', {}).setdefault('title', [])
    if c['title'] == NEW and fp in marks:
        print('Уже применено.')
        return 0
    assert c['title'] in (OLD, NEW), c['title']
    if fp not in marks:
        marks.append(fp)
    assert data['companies'][c['buyer']]['name'] == '«Коперник-Инвест 3»', data['companies'][c['buyer']]['name']
    c['title'] = NEW
    print('%s: «%s» -> «%s»' % (CID, OLD, NEW))
    if write:
        json.dump(data, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
