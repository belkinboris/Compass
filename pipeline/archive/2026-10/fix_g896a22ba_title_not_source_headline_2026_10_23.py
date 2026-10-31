# -*- coding: utf-8 -*-
"""Заголовок карточки «Дом Сыромятниковых» (g896a22ba, аукцион в Нерехте)
дословно совпадал со служебным заголовком источника в кэше (тег `title` в
`data/inbox/raw/2026-10-23-articles.jsonl`), а не с видимым на странице
заголовком статьи, и не называл продавца — находка второго чтения
(SECOND_READING_BRIEF.md), 23 октября 2026. Новый заголовок собран из слов
самой карточки (`seller`: «местные власти», `asset`: «„Дом Сыромятниковых“ —
памятник архитектуры регионального значения в Нерехте», `sum`: «1 ₽»), а не
из формулировки издания — по образцу `fix_g685f1e39_title_not_cnews_headline_2026_10_23.py`.

Карточка пока лежит в `static/data/pending.json` (приток ее еще не вынес в
`deals_promoted.json`), поэтому правится список `cards`, а не `deals`.

Без ключа — сухой прогон; запись — --write (файл перечитывается перед записью).
"""
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')

DEAL_ID = 'g896a22ba'
OLD = 'В Нерехте выставили на аукцион «Дом Сыромятниковых» за 1 рубль'
NEW = 'Местные власти выставили на торги «Дом Сыромятниковых» в Нерехте за 1 рубль'


def apply(data):
    n = 0
    for c in data['cards']:
        if c['id'] == DEAL_ID:
            if c.get('title') == NEW:
                continue
            assert c.get('title') == OLD, (c['id'], c.get('title'))
            c['title'] = NEW
            n += 1
            print('%s: %s' % (c['id'], NEW))
    return n


def main(write):
    apply(json.load(open(PENDING, encoding='utf-8')))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    data = json.load(open(PENDING, encoding='utf-8'))
    if apply(data):
        with open(PENDING, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
