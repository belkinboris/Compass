# -*- coding: utf-8 -*-
"""Торговые ряды в Нерехте, 15 млн рублей (g1a2f9d60): второе чтение нашло,
что заголовок карточки — дословная копия тега <title> источника
(«Костромская область выставила на торги исторические торговые ряды в
Нерехте за 15 млн рублей», data/inbox/raw/2026-10-24-articles.jsonl, поле
`summary`, которое на деле содержит полный текст статьи вместе с её meta
title), а не собственная фраза сборщика. Тот же дефект и тот же день —
Russ/мэрия Москвы (`g749426ce`, `pipeline/fix_g749426ce_title_2026_10_24.py`):
приёмка это не ловит, `accept_card.verbatim_runs`/`near_copy_sentences`
заголовок не сканируют (`docs/card_reading.md`, `near_copy_sentences`
явно пропускает `f == 'title'`).

Новый заголовок собран из слов уже принятых полей той же карточки —
`asset` («здание торговых рядов 1880 года в Нерехте, памятник архитектуры
(883+ кв. м)»), `seller` («Костромская область (департамент
экономического развития)») и `sum`/`eco.sum` («15 млн ₽») — без единого
нового факта, с другим скелетом предложения, чем у meta title источника
(глагол и порядок слов — по образцу уже принятых в базе заголовков
аукционов, «выставил(а) на торги», ~39 карточек в базе).

Карточка ещё в очереди предпросмотра (static/data/pending.json), поэтому
чтение и запись — через accept_card.load()/save().

Без ключа — сухой прогон, запись по --write.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
sys.path.insert(0, os.path.join(HERE, 'ingest'))
sys.path.insert(0, ROOT)

import accept_card  # noqa: E402

CARD_ID = 'g1a2f9d60'
OLD_TITLE = ('Костромская область выставила на торги исторические торговые ряды '
             'в Нерехте за 15 млн рублей')
NEW_TITLE = ('Костромская область выставила на торги здание торговых рядов 1880 года '
             'в Нерехте за 15 млн рублей')


def main():
    write = '--write' in sys.argv
    base, pending = accept_card.load()
    card, where = accept_card.find_card(CARD_ID, base, pending)
    if card is None:
        print('%s: карточки нет ни в базе, ни в очереди' % CARD_ID)
        return 1
    assert card.get('title') == OLD_TITLE, card.get('title')
    card['title'] = NEW_TITLE
    print('%s (%s): title %r -> %r' % (CARD_ID, where, OLD_TITLE, NEW_TITLE))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    accept_card.save(base, pending)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
