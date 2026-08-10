# -*- coding: utf-8 -*-
"""Карточка `g18a6d375` несла заголовок «Freedom Тимура Турлова купил
казахстанскую ИТ-компанию Bilim Group» — то же слепленное имя, что уже
исправлено в поле «Покупатель» (`pipeline/ingest/fixes/batch_g18a6d375.py`):
разбор заголовка обрезал «Holding Corp.» из источника, оставив бренд впритык
к родительному падежу имени главы компании. Владелец нашёл это в собственном
посте Telegram и назвал «ужасно написано».

Заголовок — не поле линзы, дословная цитата ему не нужна (мягкие правила
именования новых карточек, см. CLAUDE.md): здесь просто убирается лишнее
слово, а не сочиняется новый факт — «Freedom купил...» точно так же
подтверждается источником, только без слепленного родительного падежа.

Запуск: python3 pipeline/fix_bilim_group_title.py
        python3 pipeline/fix_bilim_group_title.py --write
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g18a6d375'
OLD_TITLE = 'Freedom Тимура Турлова купил казахстанскую ИТ-компанию Bilim Group'
NEW_TITLE = 'Freedom купил казахстанскую ИТ-компанию Bilim Group'


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == CARD_ID)
    if card['title'] == NEW_TITLE:
        print('УЖЕ ПРИМЕНЕНО %s' % CARD_ID)
        return
    assert card['title'] == OLD_TITLE, '%s: заголовок уже другой' % CARD_ID
    print('ПРАВИМ  %s: title %r -> %r' % (CARD_ID, OLD_TITLE, NEW_TITLE))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    card['title'] = NEW_TITLE
    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
